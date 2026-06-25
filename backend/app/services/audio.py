from __future__ import annotations

import struct
from dataclasses import dataclass, field

# Phone audio is mono 16-bit little-endian PCM at 8 kHz. 20 ms = 160 samples = 320 bytes.
SAMPLE_WIDTH = 2
FRAME_MS = 20


def pcm16_rms(frame: bytes) -> float:
    """Root-mean-square energy of a mono 16-bit little-endian PCM frame (0 for empty)."""
    count = len(frame) // SAMPLE_WIDTH
    if count == 0:
        return 0.0
    total = 0
    for i in range(0, count * SAMPLE_WIDTH, SAMPLE_WIDTH):
        sample = int.from_bytes(frame[i : i + SAMPLE_WIDTH], "little", signed=True)
        total += sample * sample
    return (total / count) ** 0.5


def wrap_pcm_as_wav(pcm: bytes, *, sample_rate: int = 8000) -> bytes:
    """Wrap raw mono 16-bit PCM in a WAV container (so it can be sent to a REST STT API)."""
    byte_rate = sample_rate * SAMPLE_WIDTH
    block_align = SAMPLE_WIDTH
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + struct.pack(
        "<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, block_align, 8 * SAMPLE_WIDTH
    )
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


def wav_to_pcm(wav: bytes) -> bytes:
    """Extract the raw PCM payload from a WAV byte string by locating the ``data`` chunk."""
    idx = wav.find(b"data")
    if idx == -1 or idx + 8 > len(wav):
        # not a WAV we recognise; assume it is already raw PCM
        return wav
    size = struct.unpack_from("<I", wav, idx + 4)[0]
    start = idx + 8
    return wav[start : start + size] if size else wav[start:]


def chunk_frames(pcm: bytes, *, frame_bytes: int = 320) -> list[bytes]:
    """Split PCM into fixed-size frames (~20 ms at 8 kHz), zero-padding the final frame."""
    if frame_bytes <= 0:
        raise ValueError("frame_bytes must be positive")
    frames = [pcm[i : i + frame_bytes] for i in range(0, len(pcm), frame_bytes)]
    if frames and len(frames[-1]) < frame_bytes:
        frames[-1] = frames[-1] + b"\x00" * (frame_bytes - len(frames[-1]))
    return frames


@dataclass(slots=True)
class UtteranceVAD:
    """Energy + silence-duration segmenter.

    Feed inbound frames; once speech has been seen and is then followed by
    ``silence_ms`` of quiet, ``add_frame`` returns the buffered utterance PCM (and resets).
    """

    sample_rate: int = 8000
    energy_threshold: float = 500.0
    silence_ms: int = 700
    min_speech_ms: int = 200
    _buffer: bytearray = field(default_factory=bytearray)
    _speech_ms: int = 0
    _silence_ms: int = 0
    _triggered: bool = False

    def _frame_ms(self, frame: bytes) -> float:
        samples = len(frame) / SAMPLE_WIDTH
        return (samples / self.sample_rate) * 1000 if self.sample_rate else 0.0

    def add_frame(self, frame: bytes) -> bytes | None:
        if not frame:
            return None
        ms = self._frame_ms(frame)
        is_speech = pcm16_rms(frame) >= self.energy_threshold

        if is_speech:
            self._triggered = True
            self._speech_ms += ms
            self._silence_ms = 0
            self._buffer.extend(frame)
            return None

        if not self._triggered:
            return None

        # trailing silence after speech
        self._silence_ms += ms
        self._buffer.extend(frame)
        if self._silence_ms >= self.silence_ms:
            if self._speech_ms >= self.min_speech_ms:
                utterance = bytes(self._buffer)
                self.reset()
                return utterance
            # too short to be real speech; discard and keep listening
            self.reset()
        return None

    def flush(self) -> bytes | None:
        """Return any buffered speech (e.g. on call end) regardless of trailing silence."""
        if self._triggered and self._speech_ms >= self.min_speech_ms:
            utterance = bytes(self._buffer)
            self.reset()
            return utterance
        self.reset()
        return None

    def reset(self) -> None:
        self._buffer = bytearray()
        self._speech_ms = 0
        self._silence_ms = 0
        self._triggered = False
