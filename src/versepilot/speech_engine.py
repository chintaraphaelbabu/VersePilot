from __future__ import annotations

import logging
import tempfile
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel

from .config import AppConfig

logger = logging.getLogger("verses")


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    average_confidence: float | None


class SpeechEngine(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray, language_hint: str | None = None) -> TranscriptionResult:
        pass


class LocalWhisperEngine(SpeechEngine):
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        model_name = config.whisper_model_name or "small"
        logger.info("Loading local Whisper model: %s (%s, %s)", model_name, config.device, config.compute_type)
        self.model = WhisperModel(
            model_name,
            device=config.device,
            compute_type=config.compute_type,
        )
        logger.info("Local Whisper model ready")

    def transcribe(self, audio: np.ndarray, language_hint: str | None = None) -> TranscriptionResult:
        beam_size = {"FAST": 1, "BALANCED": 3, "ACCURATE": 5}.get(
            self.config.whisper_mode.upper(), 3
        )
        segments, info = self.model.transcribe(
            audio,
            language=language_hint,
            beam_size=beam_size,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        segment_list = list(segments)
        text = " ".join(segment.text.strip() for segment in segment_list if segment.text.strip())
        probabilities = [segment.avg_logprob for segment in segment_list]
        confidence = None
        if probabilities:
            confidence = float(np.mean([min(1.0, max(0.0, np.exp(value))) for value in probabilities]))
        return TranscriptionResult(
            text=text.strip(),
            language=getattr(info, "language", None),
            average_confidence=confidence,
        )


class GoogleSpeechEngine(SpeechEngine):
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
