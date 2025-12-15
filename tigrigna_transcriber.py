from __future__ import annotations

"""Tigrigna audio transcription utilities.

This module wraps the Whisper speech-to-text model with helpers tailored for
Tigrigna (language code ``"ti"``).  It is written to be easy to extend toward
live/streaming transcription while providing a simple MVP for short audio
clips.
"""

from dataclasses import dataclass
from typing import List, Optional

import whisper


@dataclass
class TigrignaSegment:
    """A single segment within a Tigrigna transcript."""

    start: float
    end: float
    text: str


@dataclass
class TigrignaTranscript:
    """Structured output for a Tigrigna transcription."""

    text: str
    segments: List[TigrignaSegment]

    def as_text(self) -> str:
        """Return the transcript text as a single string."""

        return self.text


class TigrignaTranscriber:
    """Transcribe short Tigrigna audio clips with Whisper.

    Parameters
    ----------
    model_size:
        Whisper model identifier (``tiny``, ``base``, ``small``, ``medium``,
        ``large``).  Defaults to ``"small"`` which balances speed and quality.
    device:
        Optional device string (for example ``"cpu"``, ``"cuda"``).  If not
        provided Whisper will auto-detect the best option.
    """

    def __init__(self, model_size: str = "small", device: Optional[str] = None):
        self.model_size = model_size
        self.device = device
        self.model = whisper.load_model(model_size, device=device)

    def transcribe_file(
        self, audio_path: str, *, initial_prompt: Optional[str] = None
    ) -> TigrignaTranscript:
        """Transcribe a short audio file into Tigrigna.

        Parameters
        ----------
        audio_path:
            Path to the audio clip.  Any format supported by ffmpeg works
            (``.wav``, ``.mp3``, ``.m4a``, etc.).
        initial_prompt:
            Optional prompt that provides Tigrigna context for low-resource
            accents or domain-specific jargon.
        """

        result = self.model.transcribe(
            audio_path,
            language="ti",
            initial_prompt=initial_prompt,
            temperature=0.0,
        )
        segments = [
            TigrignaSegment(
                start=segment["start"],
                end=segment["end"],
                text=str(segment["text"]).strip(),
            )
            for segment in result.get("segments", [])
        ]
        text = " ".join(segment.text for segment in segments).strip()
        return TigrignaTranscript(text=text, segments=segments)

    def start_live_session(self) -> "LiveTranscriptionSession":
        """Create a live-transcription session.

        This does not implement audio capture; instead it provides a reusable
        structure that can be fed short clips (e.g., microphone chunks) and
        will accumulate a running transcript.  This keeps the MVP simple while
        leaving a clear seam to plug in a streaming audio source later.
        """

        return LiveTranscriptionSession(self)


class LiveTranscriptionSession:
    """Collect incremental Tigrigna transcriptions for live scenarios."""

    def __init__(self, transcriber: TigrignaTranscriber):
        self.transcriber = transcriber
        self._segments: List[TigrignaSegment] = []

    def ingest_clip(self, audio_path: str, *, initial_prompt: Optional[str] = None) -> TigrignaTranscript:
        """Transcribe the provided clip and append the segments.

        The running transcript can be retrieved via :py:meth:`as_text` or the
        ``segments`` property.  This lightweight interface is intended for
        future replacement with a microphone/streaming source.
        """

        transcript = self.transcriber.transcribe_file(
            audio_path, initial_prompt=initial_prompt
        )
        self._segments.extend(transcript.segments)
        return transcript

    @property
    def segments(self) -> List[TigrignaSegment]:
        return list(self._segments)

    def as_text(self) -> str:
        return " ".join(segment.text for segment in self._segments).strip()
