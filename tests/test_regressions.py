"""
Regression tests for bugs found in the debugging pass. Each test names the bug it guards.
Uses starlette's TestClient so the real WebSocket handler runs end to end (mock LLM, no TTS keys).
"""
import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from voice.llm_client import parse_budget, parse_bhk, parse_phone, parse_name


def _call(client, turns):
    """Runs one browser voice call; returns (agent replies, call_summary packet)."""
    replies = []
    with client.websocket_connect("/ws/browser-audio") as ws:
        replies.append(ws.receive_json())  # greeting
        ended = False
        for t in turns:
            ws.send_text(json.dumps({"type": "user_speech", "text": t}))
            msg = ws.receive_json()
            replies.append(msg)
            if msg["call_ended"]:
                ended = True
                break
        if not ended:
            ws.send_text(json.dumps({"type": "end_call"}))
        summary = ws.receive_json()
    assert summary["type"] == "call_summary"
    return replies, summary


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_conversations_endpoint_accepts_not_interested(client):
    # Bug: seeded outcome 'not_interested' wasn't in the enum -> GET /api/conversations returned 500.
    r = client.get("/api/conversations")
    assert r.status_code == 200
    assert any(c["outcome"] == "not_interested" for c in r.json())


def test_mock_parsers():
    # Bug: '$450k' parsed as 50k ('50' substring) and '$1.5 million 2 BHK' parsed as 1 BHK.
    assert parse_budget("2 bhk in midtown under $450k") == 450000
    assert parse_bhk("$1.5 million 2 bhk") == "2 BHK"
    assert parse_budget("$1.5 million") == 1_500_000
    assert parse_budget("call me on +91 98765-43210") is None
    assert parse_phone("my number is 98765 43210") == "9876543210"
    assert parse_name("I am looking for a flat") is None


def test_two_browser_calls_create_two_distinct_leads(client):
    # Bug: every browser session used the same hardcoded phone, so all calls overwrote one lead.
    before = {l["id"] for l in client.get("/api/leads").json()}
    _, s1 = _call(client, ["2 BHK in Midtown under $450k", "my name is Priya, 9876543210"])
    _, s2 = _call(client, ["3 bedroom in Uptown around 700k", "my name is Rahul, 9123456789"])
    assert s1["lead_id"] and s2["lead_id"] and s1["lead_id"] != s2["lead_id"]
    assert s1["outcome"] == "qualified"
    leads = {l["id"]: l for l in client.get("/api/leads").json()}
    assert leads[s1["lead_id"]]["name"] == "Priya"
    assert leads[s1["lead_id"]]["preferred_location"] == "Midtown"
    assert {s1["lead_id"], s2["lead_id"]} - before == {s1["lead_id"], s2["lead_id"]}


def test_search_uses_correct_budget(client):
    replies, _ = _call(client, ["I want a 2 BHK in Midtown under $450k"])
    tool = replies[1]["tools_called"][0]
    assert tool["arguments"] == {"location": "Midtown", "budget_max": 450000.0, "bhk": "2 BHK"}
    assert len(tool["result"]) >= 1  # Midtown 2 BHK at $420k exists in seed data


def test_empty_turn_gets_a_reply_instead_of_hanging(client):
    # Bug: empty user_speech was silently dropped, so silence handling was unreachable live.
    replies, summary = _call(client, ["", ""])
    assert "still there" in replies[1]["text"].lower()
    assert replies[2]["call_ended"] is True
    assert summary["outcome"] == "dropped"  # was tagged 'qualified' via Riya's own words


def test_escalation_outcome_survives_summary(client):
    _, summary = _call(client, ["Can I speak to a human?"])
    assert summary["outcome"] == "escalated"


def test_info_only_call_is_not_marked_qualified(client):
    _, summary = _call(client, ["Show me a 3 BHK in Downtown"])
    assert summary["outcome"] == "incomplete"


def test_dashboard_assets_are_served(client):
    # Bug: /dashboard HTML referenced /assets/*, which was never mounted -> blank page.
    import re
    html = client.get("/dashboard").text
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    assert assets, "dashboard build missing"
    for a in assets:
        assert client.get(a).status_code == 200, a


def test_twilio_status_callback_parses_form(client):
    # Bug: python-multipart was missing from requirements -> form parsing failed.
    r = client.post("/api/twilio/status-callback", data={"CallSid": "CA1", "CallStatus": "completed"})
    assert r.status_code == 200
