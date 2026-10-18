"""
G.711 mu-law codec and resampling, pure numpy (no audioop: it is removed in Python 3.13).

Twilio Media Streams carry 8 kHz, 8-bit mu-law, mono. Engines want 16-bit PCM at
16 kHz (Whisper) or emit 22.05/24 kHz (Piper), so everything passes through here.
"""
import numpy as np

PHONE_RATE = 8000
FRAME_SAMPLES = 160  # 20 ms at 8 kHz, Twilio's frame size

_BIAS = 0x84


def _build_decode_table() -> np.ndarray:
    table = np.zeros(256, dtype=np.int16)
    for i in range(256):
        u = ~i & 0xFF
        sign = u & 0x80
        exponent = (u >> 4) & 0x07
        mantissa = u & 0x0F
        sample = ((mantissa << 3) + _BIAS) << exponent
        sample -= _BIAS
        table[i] = -sample if sign else sample
    return table


_DECODE = _build_decode_table()


def _build_encode_table() -> np.ndarray:
    """Lookup over all 65536 int16 values -> mu-law byte (ITU G.711, same as CPython audioop)."""
    pcm = np.arange(-32768, 32768, dtype=np.int32) >> 2      # 14-bit
    mask = np.where(pcm < 0, 0x7F, 0xFF)
    mag = np.where(pcm < 0, -pcm, pcm)
    mag = np.minimum(mag, 8159) + 0x21
    seg_end = np.array([0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF])
    seg = np.searchsorted(seg_end, mag)                      # first seg with mag <= end
    uval = np.where(seg >= 8, 0x7F, (seg << 4) | ((mag >> (np.minimum(seg, 7) + 1)) & 0x0F))
    return (uval ^ mask).astype(np.uint8)


_ENCODE = _build_encode_table()


def ulaw_to_pcm16(data: bytes) -> np.ndarray:
    return _DECODE[np.frombuffer(data, dtype=np.uint8)]


def pcm16_to_ulaw(pcm: np.ndarray) -> bytes:
    pcm = np.asarray(pcm, dtype=np.int16)
    return _ENCODE[pcm.astype(np.int32) + 32768].tobytes()


def _lowpass(x: np.ndarray, cutoff_ratio: float, taps: int = 63) -> np.ndarray:
    """Windowed-sinc FIR. cutoff_ratio = cutoff / sample_rate (0..0.5)."""
    n = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * cutoff_ratio * n) * np.hamming(taps)
    h /= h.sum()
    return np.convolve(x, h, mode="same")


def resample(x: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Float32 resampling with anti-alias filtering when downsampling. Adequate for speech."""
    x = np.asarray(x, dtype=np.float32)
    if src_rate == dst_rate or len(x) == 0:
        return x
    if dst_rate < src_rate:
        x = _lowpass(x, 0.45 * dst_rate / src_rate)
    n_out = int(round(len(x) * dst_rate / src_rate))
    return np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x).astype(np.float32)


def pcm16_to_float(pcm: np.ndarray) -> np.ndarray:
    return np.asarray(pcm, dtype=np.float32) / 32768.0


def float_to_pcm16(x: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(x) * 32767.0, -32768, 32767).astype(np.int16)
