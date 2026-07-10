from __future__ import annotations

import logging
import tempfile
import wave
from dataclasses import dataclass

import numpy as np
import speech_recognition as sr

from config import AppConfig

logger = logging.getLogger("verses")


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    average_confidence: float | None


class WhisperEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio: np.ndarray, language_hint: str | None = None) -> TranscriptionResult:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
            with wave.open(f, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.config.whisper_sample_rate)
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())

        with sr.AudioFile(wav_path) as source:
            sr_audio = self.recognizer.record(source)

        text = ""
        language = None

        try:
            text = self.recognizer.recognize_google(sr_audio, language="te-IN")
            language = "te"
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.warning("Google STT request error: %s", e)

        if not text:
            try:
                text = self.recognizer.recognize_google(sr_audio, language="en-US")
                language = "en"
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                logger.warning("Google STT request error: %s", e)

        return TranscriptionResult(
            text=text.strip(),
            language=language,
            average_confidence=None,
        )
