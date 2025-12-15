# Investing Utilities

This repository now includes a small helper script for scraping video transcripts
from marketing landing pages.

## Tigrigna audio transcription MVP

`scripts/transcribe_tigrigna.py` provides a minimal Whisper-based flow for
turning a short audio clip into Tigrigna text while keeping the structure ready
for live/streaming inputs.

### Setup

1. Install system requirements
   * FFmpeg must be available on your `PATH` (audio decoding)
   * Python 3.10+
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install openai-whisper torch torchaudio
   ```

### Usage

Transcribe a file with the default `small` Whisper model:

```bash
python scripts/transcribe_tigrigna.py path/to/audio.wav
```

Choose a larger model, force a device, and save the output instead of printing:

```bash
python scripts/transcribe_tigrigna.py path/to/audio.wav \
  --model medium --device cuda --output transcript.txt
```

To see segment timings (helpful when building a live UI):

```bash
python scripts/transcribe_tigrigna.py path/to/audio.wav --show-segments
```

### Manual test / smoke check

Once dependencies are installed, run the CLI against a short WAV/MP3 clip and
inspect the printed transcript. For example:

```bash
python scripts/transcribe_tigrigna.py sample_audio.wav --show-segments --output transcript.txt
cat transcript.txt
```

If you want to exercise the live/stream-ready code paths, add
`--live-session-ms 500` to chunk the audio into half-second segments (this
reuses the same ingest logic a live microphone stream would rely on).

#### Running from `~/Downloads/sample.m4a`

If you want a ready-made clip in your `Downloads` folder, generate one with the
helper below (it writes a short sine-wave WAV file even though the default
extension is `.m4a`):

```bash
python scripts/create_sample_audio.py --output ~/Downloads/sample.m4a
```

Then point the transcription CLI at that file:

```bash
python scripts/transcribe_tigrigna.py ~/Downloads/sample.m4a --show-segments
```

> **Note**: Whisper relies on FFmpeg for decoding and the `whisper` package for
> inference. If those dependencies are not installed in your environment, the
> command above will fail until you install them (see Setup section).

## Extracting video transcripts

Use `scripts/extract_transcript.py` to download the transcript associated with a
video embedded on a page:

```bash
python scripts/extract_transcript.py "https://example.com/landing-page" --output transcript.txt
```

The script first looks for HTML `<track>` caption tags and, when found, downloads
the referenced WebVTT/SRT file(s). It falls back to searching for JSON blobs
that contain a `"transcript"` array.

> **Note**
> The downloader now forces TLS 1.2 when fetching pages. Some landing-page
> providers respond with `ssl.SSLError: WRONG_VERSION_NUMBER` during a TLS 1.3
> handshake; this update works around that server bug.
