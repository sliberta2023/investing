"""Utilities for downloading a transcript from the Oxford Club promo video page."""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable, Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

@dataclass
class CaptionTrack:
    language: str
    url: str


def fetch(url: str) -> bytes:
    """Fetch a URL returning raw bytes with a browser-like user agent."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request) as response:
        return response.read()


def find_wistia_media_id(html: str) -> Optional[str]:
    """Extract the first Wistia media identifier from the HTML."""
    patterns = [
        r"wistia_async_([a-zA-Z0-9]+)",
        r"https://fast\.wistia\.net/embed/iframe/([a-zA-Z0-9]+)",
        r"https://fast\.wistia\.com/embed/medias/([a-zA-Z0-9]+)\.jsonp",
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def parse_caption_tracks(media_json: dict) -> Iterable[CaptionTrack]:
    captions = media_json.get("media", {}).get("captions", [])
    for caption in captions:
        src = caption.get("src") or caption.get("url")
        if not src:
            continue
        language = caption.get("language") or caption.get("label") or "unknown"
        yield CaptionTrack(language=language, url=urllib.parse.urljoin("https://fast.wistia.com/", src))


def download_transcript(track: CaptionTrack) -> str:
    raw = fetch(track.url).decode("utf-8", errors="ignore")
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("WEBVTT"):
            continue
        if re.match(r"^\d+$", stripped):
            continue
        if "-->" in stripped:
            continue
        lines.append(stripped)
    return "\n".join(lines)


def main(url: str) -> None:
    try:
        html = fetch(url).decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to download page: {exc}")

    media_id = find_wistia_media_id(html)
    if not media_id:
        raise SystemExit("Could not locate a Wistia media ID in the provided page")

    json_url = f"https://fast.wistia.com/embed/medias/{media_id}.json"
    try:
        media_json = json.loads(fetch(json_url).decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to download Wistia metadata: {exc}")

    tracks = list(parse_caption_tracks(media_json))
    if not tracks:
        raise SystemExit("No caption tracks were found for this media")

    transcript = download_transcript(tracks[0])
    print(f"Transcript language: {tracks[0].language}")
    print("-" * 80)
    print(transcript)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} <page-url>")
    main(sys.argv[1])
