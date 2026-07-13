from __future__ import annotations

import importlib
import re
import queue
import time
from fractions import Fraction
import logging
import threading
from collections import deque
from dataclasses import dataclass

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

from config import AppConfig


@dataclass(frozen=True)
class MicrophoneInfo:
    display: int
    device_index: int
    name: str
    host_api: str


@dataclass(frozen=True)
class RecordingDevice:
    display: int
    device_index: int
    name: str
    host_api: str
    input_channels: int
    default_samplerate: float


class _EnergyVad:
    def is_speech(self, pcm16: bytes, sample_rate: int) -> bool:  # noqa: ARG002
        audio = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
        if audio.size == 0:
            return False
        audio /= 32768.0
        rms = float(np.sqrt(np.mean(np.square(audio))))
        return rms > 0.006


class MicrophoneSelector:
    _MAX_DISPLAY_NAME_LENGTH = 60
    _NOISE_TOKENS = (
        "@system32",
        "#",
        "\\",
        "/",
        ";",
        "mme",
        "directsound",
        "wasapi",
        "wdm-ks",
        "core audio",
        "hostapi",
    )

    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._cached: list[MicrophoneInfo] | None = None

    def list_microphones(self) -> list[MicrophoneInfo]:
        if self._cached is not None:
            return self._cached

        hostapis = sd.query_hostapis()
        grouped: dict[str, list[tuple[int, str, str]]] = {}
        order: list[str] = []

        for device_index, device in enumerate(sd.query_devices()):
            if device.get("max_input_channels", 0) <= 0:
                continue

            host_api = self._get_host_api_name(hostapis, device)
            base_name, suffix = self._split_name_components(device["name"])
            if self._is_specific_base(base_name):
                display_name = self._trim_display_name(base_name)
                group_key = base_name.casefold()
            else:
                suffix = self._extract_meaningful_suffix(suffix)
                if suffix:
                    display_name = self._trim_display_name(f"{base_name} ({suffix})")
                    group_key = f"{base_name.casefold()}|{suffix.casefold()}"
                else:
                    display_name = self._trim_display_name(base_name)
                    group_key = base_name.casefold()

            if group_key not in grouped:
                order.append(group_key)
                grouped[group_key] = []

            grouped[group_key].append((device_index, display_name, host_api))

        microphones: list[MicrophoneInfo] = []
        for display_index, group_key in enumerate(order):
            selected_device_index, display_name, host_api = self._select_preferred_device(grouped[group_key])
            microphones.append(
                MicrophoneInfo(
                    display=display_index,
                    device_index=selected_device_index,
                    name=self._trim_display_name(display_name),
                    host_api=host_api,
                )
            )

        self._cached = microphones
        return microphones

    def resolve_index(self, ui_index: int) -> int:
        microphones = self.list_microphones()
        if ui_index < 0 or ui_index >= len(microphones):
            raise ValueError(f"Microphone index {ui_index} is out of range")
        return microphones[ui_index].device_index

    def resolve_device(self, ui_index: int) -> RecordingDevice:
        microphones = self.list_microphones()
        if ui_index < 0 or ui_index >= len(microphones):
            raise ValueError(f"Microphone index {ui_index} is out of range")

        device_index = microphones[ui_index].device_index
        device = sd.query_devices(device_index)
        input_channels = int(device.get("max_input_channels", 0) or 0)
        if input_channels <= 0:
            raise ValueError("Selected device is not a recording device.")

        default_samplerate = float(device.get("default_samplerate") or 0.0)
        if default_samplerate <= 0:
            raise ValueError("Selected device does not report a valid default sample rate.")

        return RecordingDevice(
            display=microphones[ui_index].display,
            device_index=device_index,
            name=microphones[ui_index].name,
            host_api=microphones[ui_index].host_api,
            input_channels=input_channels,
            default_samplerate=default_samplerate,
        )

    def _get_host_api_name(self, hostapis: list[dict], device: dict) -> str:
        host_api_index = device.get("hostapi")
        if isinstance(host_api_index, int) and 0 <= host_api_index < len(hostapis):
            return str(hostapis[host_api_index].get("name", "Unknown"))
        return "Unknown"

    def _split_name_components(self, name: str) -> tuple[str, str]:
        cleaned = name.replace("®", "")
        cleaned = self._normalize_whitespace(cleaned)

        if cleaned.count("(") > cleaned.count(")"):
            return self._normalize_whitespace(cleaned.split("(", 1)[0]), ""

        base_match = re.match(r"^([^()]+?)(?:\s*\((.*)\))?$", cleaned)
        if base_match is None:
            return cleaned, ""

        base = self._normalize_whitespace(base_match.group(1))
        suffix = self._normalize_whitespace(base_match.group(2) or "")
        return base, suffix

    def _is_specific_base(self, base: str) -> bool:
        lowered = base.casefold()
        return any(char.isdigit() for char in base) or lowered.startswith("voicemeeter") or lowered.startswith("webcam")

    def _normalize_whitespace(self, value: str) -> str:
        return " ".join(value.split()).strip()

    def _extract_meaningful_suffix(self, suffix: str) -> str:
        if not suffix:
            return ""

        candidates = re.findall(r"\(([^()]*)\)", suffix)
        if not candidates:
            candidates = [suffix]

        best_candidate = ""
        best_score = -1
        for candidate in candidates:
            cleaned_candidate = self._normalize_whitespace(candidate.replace("®", ""))
            if not cleaned_candidate:
                continue

            cleaned_candidate = re.sub(r"^\d+\s*[-:.)]*\s*", "", cleaned_candidate)
            cleaned_candidate = self._normalize_whitespace(cleaned_candidate)
            if not cleaned_candidate:
                continue

            lowered = cleaned_candidate.casefold()
            if any(token in lowered for token in self._NOISE_TOKENS):
                continue

            alpha_score = sum(char.isalpha() for char in cleaned_candidate)
            if alpha_score > best_score:
                best_candidate = cleaned_candidate
                best_score = alpha_score

        return best_candidate

    def _trim_display_name(self, name: str) -> str:
        if len(name) <= self._MAX_DISPLAY_NAME_LENGTH:
            return name
        return name[: self._MAX_DISPLAY_NAME_LENGTH - 3].rstrip() + "..."

    def _select_preferred_device(self, candidates: list[tuple[int, str, str]]) -> tuple[int, str, str]:
        def score(candidate: tuple[int, str, str]) -> tuple[int, int]:
            device_index, _display_name, host_api = candidate
            is_wasapi = 1 if "wasapi" in host_api.casefold() else 0
            return (is_wasapi, -device_index)

        selected_device_index, display_name, host_api = max(candidates, key=score)
        return selected_device_index, display_name, host_api


class VoiceSegmentStream:
    def __init__(self, config: AppConfig, device: RecordingDevice) -> None:
        self.config = config
        self.device = device
        self.capture_sample_rate = int(round(device.default_samplerate))
        self.whisper_sample_rate = int(config.whisper_sample_rate)
        self.resample_ratio = self._build_resample_ratio(self.capture_sample_rate, self.whisper_sample_rate)
        vad_module = None
        try:
            vad_module = importlib.import_module("webrtcvad")
        except Exception:
            vad_module = None
        self.vad = self._build_vad(vad_module)
        self.frame_samples = max(1, int(round(self.capture_sample_rate * config.frame_ms / 1000)))
        self.padding_frames = max(1, int(config.padding_ms / config.frame_ms))
        self.silence_frames = max(1, int(config.silence_ms / config.frame_ms))
        self.min_speech_frames = max(1, int(config.min_speech_ms / config.frame_ms))
        self.max_utterance_frames = max(1, int(config.max_utterance_ms / config.frame_ms))
        self.queue: queue.Queue[np.ndarray] = queue.Queue()
        self.stop_event = threading.Event()
        self.triggered = False
        self.triggered_frames: list[np.ndarray] = []
        self.pre_roll: deque[np.ndarray] = deque(maxlen=self.padding_frames)
        self.silence_count = 0
        self.stream: sd.InputStream | None = None

    def __enter__(self) -> VoiceSegmentStream:
        self.stream = sd.InputStream(
            samplerate=self.capture_sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.frame_samples,
            device=self.device.device_index,
            callback=self._callback,
        )
        self.stream.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop_event.set()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()

    def iter_segments(self):
        while not self.stop_event.is_set():
            try:
                yield self.queue.get(timeout=0.5)
            except queue.Empty:
                yield None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            return

        frame = np.asarray(indata[:, 0], dtype=np.float32)
        if len(frame) != self.frame_samples:
            if len(frame) < self.frame_samples:
                frame = np.pad(frame, (0, self.frame_samples - len(frame)))
            else:
                frame = frame[: self.frame_samples]

        speech = self._is_speech(frame)
        self.pre_roll.append(frame.copy())

        if speech:
            if not self.triggered:
                self.triggered = True
                self.speech_start_time = time.time()
                self.triggered_frames.extend(self.pre_roll)
            self.triggered_frames.append(frame.copy())
            self.silence_count = 0
            if len(self.triggered_frames) >= self.max_utterance_frames:
                self._flush_triggered_frames()
            return

        if not self.triggered:
            return

        self.triggered_frames.append(frame.copy())
        self.silence_count += 1
        if self.silence_count < self.silence_frames:
            return

        self._flush_triggered_frames()

    def _flush_triggered_frames(self) -> None:
        if len(self.triggered_frames) >= self.min_speech_frames:
            utterance = np.concatenate(self.triggered_frames).astype(np.float32)
            utterance = self._resample_to_whisper_rate(utterance)
            speech_end_time = time.time()
            self.queue.put((utterance, getattr(self, "speech_start_time", speech_end_time), speech_end_time))

        self.triggered = False
        self.triggered_frames = []
        self.silence_count = 0

    def _is_speech(self, frame: np.ndarray) -> bool:
        audio = np.clip(frame, -1.0, 1.0)
        pcm16 = (audio * 32767).astype(np.int16).tobytes()
        return self.vad.is_speech(pcm16, self.capture_sample_rate)

    def _build_vad(self, vad_module):
        supported_rates = {8000, 16000, 32000, 48000}
        if vad_module is None or self.capture_sample_rate not in supported_rates:
            return _EnergyVad()
        return vad_module.Vad(0)

    def _build_resample_ratio(self, source_rate: int, target_rate: int) -> tuple[int, int]:
        fraction = Fraction(target_rate, source_rate).limit_denominator()
        return fraction.numerator, fraction.denominator

    def _resample_to_whisper_rate(self, audio: np.ndarray) -> np.ndarray:
        if self.capture_sample_rate == self.whisper_sample_rate:
            return audio.astype(np.float32, copy=False)

        up, down = self.resample_ratio
        resampled = resample_poly(audio, up, down).astype(np.float32)
        return np.ascontiguousarray(resampled, dtype=np.float32)

    def describe_device(self) -> dict[str, object]:
        return {
            "selected_device": self.device.device_index,
            "name": self.device.name,
            "input_channels": self.device.input_channels,
            "default_samplerate": self.device.default_samplerate,
            "capture_sample_rate": self.capture_sample_rate,
            "whisper_sample_rate": self.whisper_sample_rate,
        }