"""
Energy-based voice activity detector with an adaptive noise floor.

Works on 20 ms frames of 8 kHz PCM. Speech starts after `start_frames` consecutive
voiced frames and ends after `end_silence_ms` of quiet ("endpointing"). The noise floor
tracks background level so a noisy room doesn't read as permanent speech.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class VADConfig:
    frame_ms: int = 20
    start_frames: int = 4            # 80 ms of voice to open an utterance
    end_silence_ms: int = 700        # quiet this long closes it
    min_utterance_ms: int = 300      # shorter blips are discarded (coughs, clicks)
    max_utterance_ms: int = 15000    # force-close very long turns
    min_rms: float = 0.012           # absolute floor (float scale) below which it's never speech
    snr_factor: float = 3.0          # voiced if rms > noise_floor * snr_factor
    pre_roll_frames: int = 10        # keep 200 ms before onset so first syllable isn't clipped


@dataclass
class VADEvent:
    kind: str                         # "speech_start" | "speech_end"
    audio: Optional[np.ndarray] = None  # int16 PCM of the utterance, on speech_end


class EnergyVAD:
    def __init__(self, config: Optional[VADConfig] = None):
        self.cfg = config or VADConfig()
        self.noise_floor = 0.005
        self.in_speech = False
        self._voiced_run = 0
        self._silent_run = 0
        self._pre: List[np.ndarray] = []
        self._utt: List[np.ndarray] = []
        self.speech_ms = 0  # length of the current utterance so far

    def _is_voiced(self, frame: np.ndarray) -> bool:
        x = frame.astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(x * x)) + 1e-9)
        voiced = rms > max(self.cfg.min_rms, self.noise_floor * self.cfg.snr_factor)
        if not voiced:
            # Adapt the floor only on non-speech frames (fast down, slow up).
            alpha = 0.05 if rms > self.noise_floor else 0.3
            self.noise_floor = (1 - alpha) * self.noise_floor + alpha * rms
        return voiced

    def process(self, frame: np.ndarray) -> List[VADEvent]:
        events: List[VADEvent] = []
        voiced = self._is_voiced(frame)
        if not self.in_speech:
            self._pre.append(frame)
            if len(self._pre) > self.cfg.pre_roll_frames:
                self._pre.pop(0)
            self._voiced_run = self._voiced_run + 1 if voiced else 0
            if self._voiced_run >= self.cfg.start_frames:
                self.in_speech = True
                self._utt = list(self._pre)
                self._pre = []
                self._silent_run = 0
                self.speech_ms = len(self._utt) * self.cfg.frame_ms
                events.append(VADEvent("speech_start"))
            return events

        self._utt.append(frame)
        self.speech_ms += self.cfg.frame_ms
        self._silent_run = 0 if voiced else self._silent_run + 1
        ended = self._silent_run * self.cfg.frame_ms >= self.cfg.end_silence_ms
        if ended or self.speech_ms >= self.cfg.max_utterance_ms:
            audio = np.concatenate(self._utt)
            voiced_ms = self.speech_ms - self._silent_run * self.cfg.frame_ms
            self.reset()
            if voiced_ms >= self.cfg.min_utterance_ms:
                events.append(VADEvent("speech_end", audio))
            else:
                events.append(VADEvent("speech_end", None))  # too short: discard
        return events

    def reset(self):
        self.in_speech = False
        self._voiced_run = 0
        self._silent_run = 0
        self._utt = []
        self._pre = []
        self.speech_ms = 0
