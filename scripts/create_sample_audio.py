"""Generate a short synthetic audio tone for testing transcription flows.

Creates a mono WAV file containing a sine tone. Useful for preparing
`~/Downloads/sample.m4a` in environments without microphone access.
"""
from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path
from typing import Iterable


def generate_sine_wave(frequency_hz: float, duration_sec: float, sample_rate: int) -> Iterable[int]:
    total_samples = int(duration_sec * sample_rate)
    for i in range(total_samples):
        angle = 2 * math.pi * frequency_hz * (i / sample_rate)
        # scale to 16-bit signed integer range
        yield int(32767 * math.sin(angle))


def write_wave(path: Path, samples: Iterable[int], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(int(s).to_bytes(2, byteorder="little", signed=True) for s in samples))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a short sine-wave audio clip for testing.")
    parser.add_argument(
        "--output",
        default=Path.home() / "Downloads" / "sample.m4a",
        type=Path,
        help="Where to write the audio clip (any extension works; content is WAV)",
    )
    parser.add_argument("--duration", type=float, default=3.0, help="Clip length in seconds")
    parser.add_argument("--frequency", type=float, default=440.0, help="Sine tone frequency in Hz")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Samples per second")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    samples = list(generate_sine_wave(args.frequency, args.duration, args.sample_rate))
    write_wave(args.output, samples, args.sample_rate)
    print(f"Wrote {args.output} ({len(samples)} samples @ {args.sample_rate} Hz)")


if __name__ == "__main__":
    main()
