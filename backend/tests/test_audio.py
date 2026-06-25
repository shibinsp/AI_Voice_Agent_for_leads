from __future__ import annotations

import struct

from app.services.audio import (
    UtteranceVAD,
    chunk_frames,
    pcm16_rms,
    wav_to_pcm,
    wrap_pcm_as_wav,
)


def _tone(num_samples: int, amplitude: int) -> bytes:
    return b"".join(struct.pack("<h", amplitude) for _ in range(num_samples))


def _silence(num_samples: int) -> bytes:
    return b"\x00\x00" * num_samples


def test_pcm16_rms_silence_vs_tone():
    assert pcm16_rms(_silence(160)) == 0.0
    assert pcm16_rms(_tone(160, 4000)) > 1000.0
    assert pcm16_rms(b"") == 0.0


def test_wav_pcm_roundtrip():
    pcm = _tone(800, 1234)
    wav = wrap_pcm_as_wav(pcm, sample_rate=8000)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    assert wav_to_pcm(wav) == pcm


def test_chunk_frames_pads_last():
    pcm = b"\x01" * 700  # not a multiple of 320
    frames = chunk_frames(pcm, frame_bytes=320)
    assert len(frames) == 3
    assert all(len(f) == 320 for f in frames)


def test_vad_segments_speech_then_silence():
    vad = UtteranceVAD(sample_rate=8000, energy_threshold=500, silence_ms=200, min_speech_ms=40)
    frame_speech = _tone(160, 6000)  # 20 ms loud
    frame_quiet = _silence(160)  # 20 ms silent

    out = None
    # 300 ms of speech
    for _ in range(15):
        assert vad.add_frame(frame_speech) is None
    # silence accrues; utterance returns once silence_ms (200) is reached
    for _ in range(20):
        result = vad.add_frame(frame_quiet)
        if result is not None:
            out = result
            break
    assert out is not None
    assert len(out) > 0
    # leading silence before any speech is ignored
    assert vad.add_frame(frame_quiet) is None
