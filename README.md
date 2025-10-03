# Investing Utilities

This repository now includes a small helper script for scraping video transcripts
from marketing landing pages.

## Extracting video transcripts

Use `scripts/extract_transcript.py` to download the transcript associated with a
video embedded on a page:

```bash
python scripts/extract_transcript.py "https://example.com/landing-page" --output transcript.txt
```

The script first looks for HTML `<track>` caption tags and, when found, downloads
the referenced WebVTT/SRT file(s). It falls back to searching for JSON blobs
that contain a `"transcript"` array.
