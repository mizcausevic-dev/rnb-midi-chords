"""Repo-owned preview synthesizer.

This is not a General MIDI soundfont and not a mix engine. It renders the
canonical notes for the preview arrangement. Keys are a soft sine plus a
quiet triangle, held for the written duration. The bass guide is a sine.
Sample positions are absolute:

    sample = floor(seconds * sample_rate + 0.5)

seconds = tick / 960 * encoded_microseconds_per_quarter / 1_000_000.
Intervals are not accumulated. Sample peak is not true peak and is not LUFS.
"""

from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

SR = 44100
RENDERER_VERSION = "simple-synth-1.0.0"


def tick_to_sample(tick: int, tempo_us: int, sample_rate: int = SR) -> int:
    seconds = (tick / 960) * (tempo_us / 1_000_000)
    return int(math.floor(seconds * sample_rate + 0.5))


def container_seconds(container_ticks: int, tempo_us: int) -> float:
    return (container_ticks / 960) * (tempo_us / 1_000_000)


def _midi_freq(pitch: int) -> float:
    return 440.0 * (2.0 ** ((pitch - 69) / 12.0))


def render_preview(parts: list[dict], tempo_us: int, container_ticks: int, wav_path: Path) -> dict:
    total = tick_to_sample(container_ticks, tempo_us)
    mix = array("i", [0]) * total

    def add_bass(note: dict) -> None:
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        low = 0.0
        amp = (note["velocity"] / 127.0) * 12000.0
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            saw = 2.0 * phase - 1.0
            low += 0.16 * (saw - low)
            t = (index - start) / SR
            env = math.exp(-7.0 * t)
            if t < 0.002:
                env *= t / 0.002
            remain = (end - index) / SR
            if remain < 0.008:
                env *= remain / 0.008
            mix[index] += int(low * env * amp)

    def add_harmonic(note: dict) -> None:
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        amp = (note["velocity"] / 127.0) * 7000.0
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            triangle = 1.0 - 4.0 * abs(phase - 0.5)
            t = (index - start) / SR
            env = math.exp(-0.45 * t)
            if t < 0.03:
                env *= t / 0.03
            remain = (end - index) / SR
            if remain < 0.04:
                env *= remain / 0.04
            mix[index] += int(triangle * env * amp)

    def add_kick(note: dict) -> None:
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        phase = 0.0
        noise_state = 1 + note["performed_start"] * 17
        amp = (note["velocity"] / 127.0) * 16000.0
        for index in range(start, end):
            t = (index - start) / SR
            freq = 46.0 + 150.0 * math.exp(-t * 32.0)
            phase += freq / SR
            noise_state = (1103515245 * noise_state + 12345) & 0x7FFFFFFF
            noise = ((noise_state / 0x7FFFFFFF) * 2.0 - 1.0)
            click = noise * max(0.0, 1.0 - t / 0.004) * 0.55
            env = math.exp(-t * 26.0)
            mix[index] += int((math.sin(2.0 * math.pi * phase) * env + click) * amp)

    def add_chord(note):
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        tri = 0.0
        amp = (note["velocity"] / 127.0) * 4200.0
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            tri += inc * 2.0
            if tri >= 1.0:
                tri -= 1.0
            sine = math.sin(2.0 * math.pi * phase)
            triangle = 1.0 - 4.0 * abs(tri - 0.5)
            t = (index - start) / SR
            remain = (end - index) / SR
            env = 1.0
            if t < 0.02:
                env *= t / 0.02
            if remain < 0.04:
                env *= remain / 0.04
            mix[index] += int((sine + triangle * 0.18) * env * amp)

    def add_bass_guide(note):
        start = tick_to_sample(note["performed_start"], tempo_us)
        end = tick_to_sample(note["performed_start"] + note["duration"], tempo_us)
        end = min(total, max(end, start + 1))
        freq = _midi_freq(note["pitch"])
        inc = freq / SR
        phase = 0.0
        amp = (note["velocity"] / 127.0) * 7000.0
        for index in range(start, end):
            phase += inc
            if phase >= 1.0:
                phase -= 1.0
            t = (index - start) / SR
            remain = (end - index) / SR
            env = 1.0
            if t < 0.012:
                env *= t / 0.012
            if remain < 0.03:
                env *= remain / 0.03
            mix[index] += int(math.sin(2.0 * math.pi * phase) * env * amp)

    roles = {
        "keys-progression": add_chord,
        "bass-guide": add_bass_guide,
    }
    rendered = []
    for part in parts:
        voice = roles[part["role"]]
        for note in part["notes"]:
            voice(note)
        rendered.append({"id": part["id"], "role": part["role"], "notes": len(part["notes"])})

    peak = 0
    for sample in mix:
        magnitude = sample if sample >= 0 else -sample
        if magnitude > peak:
            peak = magnitude
    if peak == 0:
        raise RuntimeError("preview mix is silent")
    scale = 1.0 if peak <= 28000 else 28000.0 / peak
    pcm = array("h")
    for sample in mix:
        value = int(sample * scale)
        if value > 32767:
            value = 32767
        elif value < -32768:
            value = -32768
        pcm.append(value)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())
    sample_peak = int(peak * scale)
    return {
        "renderer": RENDERER_VERSION,
        "sample_rate": SR,
        "channels": 1,
        "sample_format": "signed 16-bit little-endian PCM",
        "samples": total,
        "seconds": container_seconds(container_ticks, tempo_us),
        "rounding": "sample = floor(seconds * sample_rate + 0.5), computed from tick 0; intervals are not summed",
        "sample_peak": sample_peak,
        "sample_peak_dbfs": 20.0 * math.log10(sample_peak / 32768.0),
        "sample_peak_note": "This is a sample peak of the integer mix after scaling. It is not a true-peak measurement and it is not LUFS.",
        "voices": rendered,
        "mapping": {
            "keys-progression": "sine plus a quiet triangle, short attack, held for the written duration",
            "bass-guide": "sine at the written pitch, short attack, held for the written duration",
        },
        "mapping_note": "These voices are preview mappings. They are not encoded in the MIDI file.",
    }
