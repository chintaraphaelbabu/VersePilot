from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from config import AppConfig
from books import whisper_initial_prompt


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    average_confidence: float | None


class WhisperEngine:
    def __init__(self, config: AppConfig) -> None:
        from faster_whisper import WhisperModel

        self.config = config
        
        mode = (config.whisper_mode or "BALANCED").upper()
        if mode == "FAST":
            default_model = "small"
            self.beam_size = 1
        elif mode == "ACCURATE":
            default_model = "medium"
            self.beam_size = 5
        else:  # BALANCED
            default_model = "small"
            self.beam_size = 3

        model_name = config.whisper_model_name or default_model

        self.model = WhisperModel(
            model_name,
            device=config.device,
            compute_type=config.compute_type,
        )

    def transcribe(self, audio: np.ndarray, language_hint: str | None = None) -> TranscriptionResult:
        segments, info = self.model.transcribe(
            audio,
            language=language_hint,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": self.config.silence_ms},
            beam_size=self.beam_size,
            temperature=0,
            best_of=self.beam_size,
            condition_on_previous_text=False,
            initial_prompt=whisper_initial_prompt(),
        )
        segment_list = list(segments)
        text = " ".join(segment.text for segment in segment_list).strip()

        if segment_list:
            avg_logprob = sum(float(segment.avg_logprob) for segment in segment_list) / len(segment_list)
            average_confidence = max(0.0, min(1.0, math.exp(avg_logprob)))
        else:
            average_confidence = None

        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", None),
            average_confidence=average_confidence,
        )