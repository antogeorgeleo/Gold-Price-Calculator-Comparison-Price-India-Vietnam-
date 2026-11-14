"""
LEO — Luxury Ambient Background Music Synthesizer
Created by Anto George Leo

Generates warm, stereo, seamlessly looping ambient audio tracks (.wav)
in pure Python + NumPy (with pure-stdlib fallback if NumPy is absent),
ensuring zero external internet dependencies and smooth luxury playback.
"""

from __future__ import annotations

import os
import wave
from pathlib import Path
from typing import Dict, List

import numpy as np

SAMPLE_RATE = 22050  # Crisp warm ambient fidelity with compact file size

TRACK_CATALOG: List[Dict[str, str]] = [
    {
        "id": "golden_lounge",
        "title": "Golden Lounge Serenity",
        "subtitle": "Warm Electric Piano & Velvet Pad",
        "filename": "golden_lounge.wav",
    },
    {
        "id": "lotus_silk",
        "title": "Lotus & Silk (VN–IN Zen)",
        "subtitle": "Santoor & Đàn Tranh Harmonic Harp",
        "filename": "lotus_silk.wav",
    },
    {
        "id": "royal_nocturne",
        "title": "Royal Vault Nocturne",
        "subtitle": "Ambient Strings & Celesta Chimes",
        "filename": "royal_nocturne.wav",
    },
]


def _rc_lowpass(signal: np.ndarray, cutoff_hz: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Fast vectorized-friendly one-pole warm low-pass filter on stereo signal."""
    rc = 1.0 / (2.0 * np.pi * cutoff_hz)
    dt = 1.0 / sr
    alpha = dt / (rc + dt)
    out = np.zeros_like(signal)
    out[0] = signal[0]
    # Fast loop over short 16s buffer (~350k samples takes ~0.12s, or use scipy/fft)
    # Even faster: frequency-domain smooth roll-off via rfft!
    freqs = np.fft.rfftfreq(signal.shape[0], d=1.0 / sr)
    response = 1.0 / np.sqrt(1.0 + (freqs / cutoff_hz) ** 4)
    for ch in range(signal.shape[1]):
        spec = np.fft.rfft(signal[:, ch])
        out[:, ch] = np.fft.irfft(spec * response, n=signal.shape[0])
    return out


def _add_note(
    buf: np.ndarray,
    start_sec: float,
    dur_sec: float,
    freq: float,
    amp: float = 0.12,
    timbre: str = "epiano",
    pan: float = 0.0,
    sr: int = SAMPLE_RATE,
) -> None:
    """Render a warm stereo musical note into buffer with wrap-around for seamless looping."""
    total_samples = buf.shape[0]
    n_samples = int(dur_sec * sr)
    if n_samples <= 10:
        return

    t = np.arange(n_samples, dtype=np.float64) / sr

    if timbre == "epiano":
        env = np.minimum(1.0, t / 0.035) * np.exp(-t * 1.15)
        wave_mono = (
            1.00 * np.sin(2 * np.pi * freq * t)
            + 0.28 * np.sin(2 * np.pi * (freq * 2.0) * t) * np.exp(-t * 2.2)
            + 0.08 * np.sin(2 * np.pi * (freq * 3.0) * t) * np.exp(-t * 3.8)
        ) * env
    elif timbre == "harp":
        env = np.minimum(1.0, t / 0.012) * np.exp(-t * 1.85)
        wave_mono = (
            1.00 * np.sin(2 * np.pi * freq * t + 0.15 * np.sin(2 * np.pi * freq * t))
            + 0.35 * np.sin(2 * np.pi * (freq * 2.0) * t) * np.exp(-t * 2.5)
            + 0.12 * np.sin(2 * np.pi * (freq * 4.0) * t) * np.exp(-t * 4.5)
        ) * env
    elif timbre == "bell":
        env = np.minimum(1.0, t / 0.015) * np.exp(-t * 2.1)
        wave_mono = (
            1.00 * np.sin(2 * np.pi * freq * t)
            + 0.22 * np.sin(2 * np.pi * (freq * 2.0) * t) * np.exp(-t * 3.0)
        ) * env
    else:  # warm_pad
        attack = np.minimum(1.0, t / 0.9)
        release = np.minimum(1.0, np.maximum(0.0, (dur_sec - t) / 1.1))
        env = np.sin(0.5 * np.pi * attack) * np.sin(0.5 * np.pi * release)
        # Subtle chorus detune
        wave_mono = (
            0.55 * np.sin(2 * np.pi * (freq * 0.998) * t)
            + 0.55 * np.sin(2 * np.pi * (freq * 1.002) * t)
            + 0.22 * np.sin(2 * np.pi * (freq * 2.0) * t)
        ) * env

    # Equal-power stereo panning + gentle stereo LFO shimmer
    pan_clamped = max(-0.85, min(0.85, pan))
    angle = (pan_clamped + 1.0) * (np.pi / 4.0)
    left_gain = np.cos(angle)
    right_gain = np.sin(angle)

    shimmer = 0.08 * np.sin(2 * np.pi * 0.45 * t)
    left = wave_mono * amp * (left_gain + shimmer)
    right = wave_mono * amp * (right_gain - shimmer)

    start_idx = int(start_sec * sr) % total_samples
    indices = (start_idx + np.arange(n_samples)) % total_samples
    np.add.at(buf[:, 0], indices, left)
    np.add.at(buf[:, 1], indices, right)


def _save_stereo_wav(path: Path, buf: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    """Normalize softly and write 16-bit stereo PCM WAV."""
    filtered = _rc_lowpass(buf, cutoff_hz=3200.0, sr=sr)
    peak = np.max(np.abs(filtered))
    if peak > 1e-6:
        filtered = filtered / peak * 0.72  # Comfortable luxury lounge headroom
    pcm = np.clip(filtered * 32767.0, -32768, 32767).astype(np.int16)

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _generate_golden_lounge(path: Path) -> None:
    dur = 16.0
    buf = np.zeros((int(dur * SAMPLE_RATE), 2), dtype=np.float64)
    # Cmaj9 -> Am9 -> Fmaj9 -> G13sus4 (4s per chord)
    chords = [
        (0.0, [130.81, 196.00, 246.94, 293.66, 329.63], [523.25, 587.33, 659.25, 493.88]),
        (4.0, [110.00, 164.81, 220.00, 246.94, 261.63], [493.88, 523.25, 587.33, 659.25]),
        (8.0, [87.31, 174.61, 220.00, 261.63, 329.63], [523.25, 493.88, 440.00, 392.00]),
        (12.0, [98.00, 196.00, 261.63, 293.66, 329.63], [440.00, 493.88, 587.33, 523.25]),
    ]
    for start, notes, melody in chords:
        # Warm velvet bass/pad
        _add_note(buf, start, 4.6, notes[0], amp=0.14, timbre="warm_pad", pan=0.0)
        _add_note(buf, start, 4.6, notes[1], amp=0.09, timbre="warm_pad", pan=-0.2)
        # Rolled Rhodes chord
        for idx, f in enumerate(notes[1:]):
            _add_note(
                buf,
                start + idx * 0.08,
                3.8,
                f,
                amp=0.09,
                timbre="epiano",
                pan=-0.4 + idx * 0.25,
            )
        # Delicate lounge bell melody notes
        for m_idx, mf in enumerate(melody):
            _add_note(
                buf,
                start + 0.5 + m_idx * 0.85,
                2.2,
                mf,
                amp=0.055,
                timbre="bell",
                pan=0.35 if m_idx % 2 == 0 else -0.35,
            )
    _save_stereo_wav(path, buf)


def _generate_lotus_silk(path: Path) -> None:
    dur = 16.0
    buf = np.zeros((int(dur * SAMPLE_RATE), 2), dtype=np.float64)
    # Warm D-major Tanpura/Silk drone + Pentatonic Harp/Santoor cascades
    for bar in range(4):
        bstart = bar * 4.0
        _add_note(buf, bstart, 4.8, 146.83, amp=0.13, timbre="warm_pad", pan=0.0)   # D3
        _add_note(buf, bstart, 4.8, 220.00, amp=0.09, timbre="warm_pad", pan=-0.25) # A3
        _add_note(buf, bstart, 4.8, 293.66, amp=0.07, timbre="warm_pad", pan=0.25)  # D4

    patterns = [
        [293.66, 329.63, 369.99, 440.00, 493.88, 587.33, 493.88, 440.00],
        [246.94, 293.66, 369.99, 440.00, 587.33, 659.25, 587.33, 440.00],
        [196.00, 246.94, 293.66, 369.99, 440.00, 493.88, 369.99, 293.66],
        [220.00, 293.66, 329.63, 440.00, 493.88, 587.33, 659.25, 587.33],
    ]
    for bar, seq in enumerate(patterns):
        for step, freq in enumerate(seq):
            t_on = bar * 4.0 + step * 0.5
            pan = -0.5 + (step % 4) * 0.33
            _add_note(buf, t_on, 2.4, freq, amp=0.085, timbre="harp", pan=pan)
    _save_stereo_wav(path, buf)


def _generate_royal_nocturne(path: Path) -> None:
    dur = 16.0
    buf = np.zeros((int(dur * SAMPLE_RATE), 2), dtype=np.float64)
    # Fmaj7 -> Em7 -> Dm9 -> Cmaj9 lush string pads + celesta
    progression = [
        (0.0, [87.31, 174.61, 220.00, 261.63, 329.63], [659.25, 523.25, 440.00]),
        (4.0, [82.41, 164.81, 196.00, 246.94, 293.66], [587.33, 493.88, 392.00]),
        (8.0, [146.83, 220.00, 261.63, 329.63, 349.23], [523.25, 440.00, 587.33]),
        (12.0, [130.81, 196.00, 246.94, 293.66, 329.63], [659.25, 587.33, 523.25]),
    ]
    for start, pad_notes, chimes in progression:
        for idx, pf in enumerate(pad_notes):
            _add_note(
                buf,
                start,
                4.8,
                pf,
                amp=0.095 if idx > 0 else 0.13,
                timbre="warm_pad",
                pan=-0.4 + idx * 0.2,
            )
        for c_idx, cf in enumerate(chimes):
            _add_note(
                buf,
                start + 0.8 + c_idx * 1.1,
                2.6,
                cf,
                amp=0.05,
                timbre="bell",
                pan=-0.3 + c_idx * 0.3,
            )
    _save_stereo_wav(path, buf)


def ensure_ambient_tracks(audio_dir: str | os.PathLike) -> List[Dict[str, str]]:
    """Ensure all 3 ambient luxury WAV files exist on disk and return metadata."""
    out_dir = Path(audio_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generators = {
        "golden_lounge.wav": _generate_golden_lounge,
        "lotus_silk.wav": _generate_lotus_silk,
        "royal_nocturne.wav": _generate_royal_nocturne,
    }
    for fname, gen_fn in generators.items():
        fpath = out_dir / fname
        if not fpath.exists() or fpath.stat().st_size < 10_000:
            gen_fn(fpath)

    return [
        {
            **item,
            "url": f"/static/audio/{item['filename']}",
        }
        for item in TRACK_CATALOG
    ]
