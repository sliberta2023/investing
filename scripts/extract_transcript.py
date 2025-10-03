#!/usr/bin/env python3
"""Download and extract a transcript from a marketing landing-page video.

The script is intentionally dependency free so it can be dropped into any
project.  It attempts to locate caption tracks (<track> elements) in the
returned HTML and, when found, downloads the referenced WebVTT/SRT files.

Usage
-----
    python scripts/extract_transcript.py <url> [--output transcript.txt]

If no transcript could be located the script raises ``RuntimeError`` with a
helpful message.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urljoin
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


class _HTMLTrackCollector(HTMLParser):
    """Collect caption/subtitle ``<track>`` tags from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.tracks: List[Tuple[str, Optional[str]]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "track":
            return
        attr_map = {key.lower(): value for key, value in attrs}
        kind = (attr_map.get("kind") or "").lower()
        if kind not in {"subtitles", "captions"}:
            return
        src = attr_map.get("src")
        label = attr_map.get("label")
        if src:
            self.tracks.append((src, label))


def fetch(url: str) -> bytes:
    """Download ``url`` returning the raw bytes."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request) as response:  # type: ignore[no-untyped-call]
        return response.read()


def parse_webvtt(data: str) -> List[str]:
    """Convert a WebVTT/SRT caption file into a list of text cues."""
    cues: List[str] = []
    buffer: List[str] = []
    skipping_note = False
    for raw_line in data.splitlines():
        line = raw_line.strip("\ufeff \t")  # also remove BOM if present
        if not line:
            if buffer:
                cues.append(" ".join(buffer).strip())
                buffer.clear()
            skipping_note = False
            continue
        if line.upper().startswith("WEBVTT"):
            continue
        if line.upper().startswith("NOTE"):
            skipping_note = True
            continue
        if skipping_note:
            continue
        if "-->" in line:  # timing line
            continue
        # Most SRT files number the cues.  Skip pure integers.
        if line.isdigit():
            continue
        buffer.append(line)
    if buffer:
        cues.append(" ".join(buffer).strip())
    return [cue for cue in cues if cue]


def extract_captions(url: str, html: str) -> Iterable[str]:
    """Locate <track> elements and download each caption track."""
    parser = _HTMLTrackCollector()
    parser.feed(html)
    if not parser.tracks:
        return []
    transcripts: List[str] = []
    for src, label in parser.tracks:
        caption_url = urljoin(url, src)
        try:
            content = fetch(caption_url)
        except Exception as exc:  # pragma: no cover - network issue feedback
            print(f"Skipping caption {caption_url!r}: {exc}", file=sys.stderr)
            continue
        text = parse_webvtt(content.decode("utf-8", "ignore"))
        if text:
            header = f"[{label}]" if label else None
            if header:
                transcripts.append(header)
            transcripts.extend(text)
    return transcripts


_JSON_TRANSCRIPT_RE = re.compile(r'"transcript"\s*:\s*(\[[^]]*\])', re.IGNORECASE)


def extract_json_transcript(html: str) -> Optional[List[str]]:
    """Fallback: search for ``"transcript": [...]`` fragments in JSON blobs."""
    match = _JSON_TRANSCRIPT_RE.search(html)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    lines: List[str] = []
    for item in payload:
        if isinstance(item, dict):
            text = item.get("text") or item.get("body")
            if text:
                lines.append(str(text))
        elif isinstance(item, str):
            lines.append(item)
    return lines or None


@dataclass
class TranscriptResult:
    lines: List[str]

    def as_text(self) -> str:
        return "\n".join(self.lines)


def extract_transcript(url: str) -> TranscriptResult:
    html_bytes = fetch(url)
    html = html_bytes.decode("utf-8", "ignore")

    caption_lines = list(extract_captions(url, html))
    if caption_lines:
        return TranscriptResult(caption_lines)

    json_lines = extract_json_transcript(html)
    if json_lines:
        return TranscriptResult(json_lines)

    raise RuntimeError(
        "Unable to find a transcript in the provided page. "
        "Inspect the HTML for custom transcript structures."
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Page URL that embeds the video")
    parser.add_argument(
        "--output",
        "-o",
        help="Optional path to save the transcript; defaults to stdout",
    )
    args = parser.parse_args(None if argv is None else list(argv))

    try:
        result = extract_transcript(args.url)
    except Exception as exc:
        parser.error(str(exc))
        return 2

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(result.as_text())
    else:
        print(result.as_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
