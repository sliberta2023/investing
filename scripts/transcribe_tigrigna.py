#!/usr/bin/env python3
"""Transcribe a short audio clip into Tigrigna.

Examples
--------
Transcribe a file and print the Tigrigna text:

```
python scripts/transcribe_tigrigna.py sample.wav
```

Specify a different Whisper model and write the raw transcript to disk:

```
python scripts/transcribe_tigrigna.py sample.wav --model medium --output transcript.txt
```
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tigrigna_transcriber import LiveTranscriptionSession, TigrignaTranscriber


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", help="Path to the audio clip to transcribe")
    parser.add_argument(
        "--model",
        default="small",
        help="Whisper model size (tiny, base, small, medium, large)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional computation device override (cpu, cuda, etc.)",
    )
    parser.add_argument(
        "--initial-prompt",
        help="Optional Tigrigna prompt to bias decoding",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Save the transcript to this file instead of printing",
    )
    parser.add_argument(
        "--show-segments",
        action="store_true",
        help="Display timing information for each segment",
    )
    return parser


def format_segments(session: LiveTranscriptionSession) -> str:
    lines = []
    for segment in session.segments:
        lines.append(f"[{segment.start:6.2f} -> {segment.end:6.2f}] {segment.text}")
    return "\n".join(lines)


def transcribe_clip(
    audio_path: str, *, model: str, device: Optional[str], initial_prompt: Optional[str]
) -> LiveTranscriptionSession:
    transcriber = TigrignaTranscriber(model_size=model, device=device)
    session = transcriber.start_live_session()
    session.ingest_clip(audio_path, initial_prompt=initial_prompt)
    return session


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(None if argv is None else list(argv))

    session = transcribe_clip(
        args.audio,
        model=args.model,
        device=args.device,
        initial_prompt=args.initial_prompt,
    )
    output = format_segments(session) if args.show_segments else session.as_text()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
