from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


LanguageOption = Literal["en", "te"] | None


@dataclass
class AppConfig:
    whisper_model_name: str | None = None
    device: str = "cpu"
    compute_type: str = "int8"
    whisper_sample_rate: int = 16_000
    frame_ms: int = 30
    padding_ms: int = 150
    silence_ms: int = 200
    min_speech_ms: int = 400
    max_utterance_ms: int = 60000
    log_level: str = "INFO"
    language: LanguageOption = None
    freeshow_host: str = "127.0.0.1"
    freeshow_port: int = 5506
    whisper_mode: str = "ACCURATE"
    reference_builder_timeout: int = 20
    chapter_silence_timeout: float = 3.0
    min_confidence: float = 0.80
    text_match_score_full: int = 85
    text_match_score_scoped: int = 50
    buffer_max_chars: int = 300
    scope_text_min_len: int = 12
    full_text_min_len: int = 20


def load_config() -> AppConfig:
    whisper_mode = os.getenv("VERSE_WHISPER_MODE", "BALANCED")
    mode_upper = whisper_mode.upper()
    if mode_upper == "FAST":
        default_model = "small"
    elif mode_upper == "ACCURATE":
        default_model = "medium"
    else:
        default_model = "medium"

    return AppConfig(
        whisper_model_name=os.getenv("VERSE_WHISPER_MODEL_NAME", os.getenv("VERSE_MODEL_SIZE", default_model)),
        device=os.getenv("VERSE_DEVICE", "cpu"),
        compute_type=os.getenv("VERSE_COMPUTE_TYPE", "int8"),
        whisper_sample_rate=int(os.getenv("VERSE_WHISPER_SAMPLE_RATE", "16000")),
        frame_ms=int(os.getenv("VERSE_FRAME_MS", "30")),
        padding_ms=int(os.getenv("VERSE_PADDING_MS", "150")),
        silence_ms=int(os.getenv("VERSE_SILENCE_MS", "200")),
        min_speech_ms=int(os.getenv("VERSE_MIN_SPEECH_MS", "400")),
        max_utterance_ms=int(os.getenv("VERSE_MAX_UTTERANCE_MS", "60000")),
        log_level=os.getenv("VERSE_LOG_LEVEL", "INFO"),
        language=normalize_language_option(os.getenv("VERSE_LANGUAGE")),
        freeshow_host=os.getenv("FREESHOW_HOST", "127.0.0.1"),
        freeshow_port=int(os.getenv("FREESHOW_PORT", "5506")),
        whisper_mode=whisper_mode,
        reference_builder_timeout=int(os.getenv("VERSE_BUILDER_TIMEOUT", "20")),
        chapter_silence_timeout=float(os.getenv("VERSE_CHAPTER_TIMEOUT", "3.0")),
        min_confidence=float(os.getenv("VERSE_MIN_CONFIDENCE", "0.80")),
        text_match_score_full=int(os.getenv("VERSE_TEXT_MATCH_FULL", "85")),
        text_match_score_scoped=int(os.getenv("VERSE_TEXT_MATCH_SCOPED", "50")),
        buffer_max_chars=int(os.getenv("VERSE_BUFFER_MAX", "300")),
        scope_text_min_len=int(os.getenv("VERSE_SCOPE_MIN_LEN", "12")),
        full_text_min_len=int(os.getenv("VERSE_FULL_MIN_LEN", "20")),
    )


def normalize_language_option(value: str | None) -> LanguageOption:
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "none", "auto"}:
        return None
    if normalized in {"en", "english"}:
        return "en"
    if normalized in {"te", "telugu"}:
        return "te"
    raise ValueError("language must be 'AUTO', 'ENGLISH', or 'TELUGU'")