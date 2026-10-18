"""
Phone pipeline tests. They use fake STT/TTS engines (no models, no keys) and drive
/ws/twilio with the exact Twilio Media Streams message format.
"""
import base64
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from voice.telephony import engines
from voice.telephony.codec import pcm16_to_ulaw, ulaw_to_pcm16, float_to_pcm16
from voice.telephony.engines import normalize_transcript
from voice.telephony.vad import EnergyVAD


def test_mulaw_roundtrip_and_reference_table():
    x = np.arange(-32768, 32768, 7, dtype=np.int16)
    y = ulaw_to_pcm16(pcm16_to_ulaw(x))
    # mu-law is lossy but bounded: < 3.2% of full scale on loud samples
    assert np.max(np.abs(x.astype(int) - y)) < 1100
    # Known G.711 code points: silence encodes to 0xFF, full-scale negative to 0x00
    assert pcm16_to_ulaw(np.array([0], dtype=np.int16)) == b"\xff"
    assert pcm16_to_ulaw(np.array([-32768], dtype=np.int16)) == b"\x00"


def test_transcript_normalizer_fixes_phone_homophones():
    assert "2 BHK" in normalize_transcript("I wanted to, BHK apartment")
    assert "2 BHK" in normalize_transcript("a two bhk in Midtown")
    assert "4 BHK" in normalize_transcript("looking for for BSK")
    assert "3 BHK" in normalize_transcript("3 BHQ please")


def _tone(seconds, amp=0.3, rate=8000):
    t = np.arange(int(seconds * rate)) / rate
    # speech-like: 200 Hz carrier with 4 Hz syllable envelope
    return float_to_pcm16(amp * np.sin(2 * np.pi * 200 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t)))


def _quiet(seconds, rate=8000):
    return float_to_pcm16(np.random.default_rng(0).normal(0, 0.002, int(seconds * rate)))


def _run_vad(pcm):
    vad, events = EnergyVAD(), []
    for i in range(0, len(pcm) - 159, 160):
        events += vad.process(pcm[i:i + 160])
    return events


def test_vad_detects_utterance_and_ignores_noise_and_clicks():
    ev = _run_vad(np.concatenate([_quiet(1), _tone(1.2), _quiet(1.2)]))
    kinds = [e.kind for e in ev]
    assert kinds == ["speech_start", "speech_end"]
    assert ev[1].audio is not None and len(ev[1].audio) / 8000 > 1.0
    assert _run_vad(_quiet(3)) == []
    clicks = _run_vad(np.concatenate([_quiet(1), _tone(0.1), _quiet(1.5)]))
    assert all(e.audio is None for e in clicks if e.kind == "speech_end")


class FakeSTT(engines.BaseSTT):
    name = "fake"

    def __init__(self, lines):
        self.lines = list(lines)

    async def transcribe(self, pcm8k):
        return self.lines.pop(0) if self.lines else ""


class FakeTTS(engines.BaseTTS):
    name = "fake"

    async def synthesize_ulaw(self, text):
        return pcm16_to_ulaw(_quiet(0.4))


@pytest.fixture
def phone(monkeypatch):
    def make(lines):
        monkeypatch.setattr(engines, "get_stt", lambda: FakeSTT(lines))
        monkeypatch.setattr(engines, "get_tts", lambda: FakeTTS())
        return TestClient(app)
    return make


def _start(ws):
    ws.send_text(json.dumps({"event": "connected", "protocol": "Call", "version": "1.0.0"}))
    ws.send_text(json.dumps({"event": "start", "streamSid": "MZ1", "start": {
        "streamSid": "MZ1", "callSid": "CA1", "customParameters": {"debug": "1", "from": "+919800000001"},
        "mediaFormat": {"encoding": "audio/x-mulaw", "sampleRate": 8000, "channels": 1}}}))


def _send_pcm(ws, pcm):
    ulaw = pcm16_to_ulaw(pcm)
    for i in range(0, len(ulaw), 160):
        ws.send_text(json.dumps({"event": "media", "streamSid": "MZ1",
                                 "media": {"track": "inbound", "payload": base64.b64encode(ulaw[i:i + 160]).decode()}}))


def _until(ws, pred, limit=400):
    """Reads server messages (echoing marks like Twilio) until pred(msg) is true."""
    for _ in range(limit):
        m = json.loads(ws.receive_text())
        if m["event"] == "mark":
            ws.send_text(json.dumps({"event": "mark", "streamSid": "MZ1", "mark": m["mark"]}))
        if pred(m):
            return m
    raise AssertionError("expected message never arrived")


def _is(kind):
    return lambda m: m["event"] == "x-debug" and m["type"] == kind


def test_phone_call_full_flow(phone):
    client = phone(["I want a two BHK in Midtown under 450k", "My name is Priya"])
    with client, client.websocket_connect("/ws/twilio") as ws:
        _start(ws)
        greeting = _until(ws, _is("agent"))
        assert "Riya" in greeting["text"]
        _send_pcm(ws, np.concatenate([_tone(1.0), _quiet(1.0)]))
        caller = _until(ws, _is("caller"))
        assert "2 BHK" in caller["text"]
        tools = _until(ws, _is("tools"))
        assert tools["tools"][0]["arguments"] == {"location": "Midtown", "budget_max": 450000.0, "bhk": "2 BHK"}
        reply = _until(ws, lambda m: m["event"] == "media")  # Riya's audio actually goes out
        assert reply["streamSid"] == "MZ1"
        _send_pcm(ws, np.concatenate([_tone(1.0), _quiet(1.0)]))
        _until(ws, lambda m: m["event"] == "mark" and m["mark"]["name"] == "hangup")
    leads = client.get("/api/leads?search=Priya").json()
    assert leads and leads[0]["phone"] == "+919800000001" and leads[0]["bhk_preference"] == "2 BHK"


def test_phone_barge_in_sends_clear(phone):
    client = phone(["Show me something in Uptown", "wait stop"])
    with client, client.websocket_connect("/ws/twilio") as ws:
        _start(ws)
        _until(ws, _is("agent"))
        _send_pcm(ws, np.concatenate([_tone(1.0), _quiet(1.0)]))
        # Riya's answer is now queued on the line; do NOT echo its mark (still "playing")
        for _ in range(400):
            m = json.loads(ws.receive_text())
            if m["event"] == "mark":
                break
        _send_pcm(ws, _tone(0.8))  # caller talks over her
        for _ in range(400):
            m = json.loads(ws.receive_text())
            if m["event"] == "clear":
                assert m["streamSid"] == "MZ1"
                break
        else:
            raise AssertionError("no clear sent on barge-in")


def test_twiml_streams_to_phone_pipeline():
    with TestClient(app) as client:
        r = client.post("/api/twilio/incoming-call", data={"From": "+919811111111"})
        assert "/ws/twilio" in r.text and 'value="+919811111111"' in r.text
        assert client.get("/phone-sim").status_code == 200
