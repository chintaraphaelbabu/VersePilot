from __future__ import annotations

import argparse
import logging
import time
import sounddevice as sd

from config import load_config
from freeshow import FreeShowClient
from mic import MicrophoneSelector, RecordingDevice, VoiceSegmentStream
from parser import BibleReferenceParser
from utils import setup_logging
from whisper_engine import WhisperEngine
from sermon_context import SermonContext


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice-to-Bible-reference transcription")
    parser.add_argument("--list-mics", action="store_true", help="List available microphones and exit")
    parser.add_argument("--mic", type=int, help="Microphone index from the listed devices")
    parser.add_argument("--model", help="Override the Faster-Whisper model size")
    parser.add_argument("--mode", choices=["FAST", "BALANCED", "ACCURATE", "fast", "balanced", "accurate"], help="Whisper latency mode")
    parser.add_argument("--language", help="Force en, te, or use None for auto-detect")
    parser.add_argument("--dry-run", action="store_true", help="Do not send references to FreeShow")
    return parser.parse_args()


def choose_microphone(selector: MicrophoneSelector, mic_index: int | None) -> RecordingDevice:
    microphones = selector.list_microphones()
    if not microphones:
        raise RuntimeError("No input microphones were found")

    if mic_index is not None:
        return selector.resolve_device(mic_index)

    print("\nAvailable microphones:\n")
    for item in microphones:
        print(f"[{item.display}] {item.name}")

    while True:
        try:
            choice = int(input("\nChoose microphone: "))
            return selector.resolve_device(choice)
        except ValueError:
            print("Enter a valid microphone index.")


def main() -> int:
    args = parse_args()
    config = load_config()

    if args.mode:
        config.whisper_mode = args.mode.upper()
        if not args.model:
            if config.whisper_mode == "FAST":
                config.whisper_model_name = "small"
            elif config.whisper_mode == "ACCURATE":
                config.whisper_model_name = "medium"
            else:
                config.whisper_model_name = "small"

    if args.model:
        config.whisper_model_name = args.model

    if args.language:
        from config import normalize_language_option
        config.language = normalize_language_option(args.language)

    setup_logging(config.log_level)
    logger = logging.getLogger("verses")

    selector = MicrophoneSelector(config.whisper_sample_rate)
    if args.list_mics:
        for item in selector.list_microphones():
            print(f"[{item.display}] {item.name}")
        return 0

    engine = WhisperEngine(config)
    parser = BibleReferenceParser()
    freeshow = FreeShowClient(config) if not args.dry_run else None
    sermon_context = SermonContext()

    last_reference: str | None = None

    try:
        while True:
            try:
                device = choose_microphone(selector, args.mic)
            except ValueError as exc:
                print(str(exc))
                if args.mic is not None:
                    return 1
                continue

            logger.info("Selected device:")
            logger.info("Name: %s", device.name)
            logger.info("Input channels: %s", device.input_channels)
            logger.info("Default sample rate: %s", device.default_samplerate)
            logger.info("Using capture sample rate: %s", int(round(device.default_samplerate)))
            logger.info("Using Whisper sample rate: %s", config.whisper_sample_rate)
            logger.info("Whisper mode: %s", config.whisper_mode)
            logger.info("Whisper model: %s", config.whisper_model_name)

            try:
                logger.info("Listening on microphone %s", device.device_index)
                logger.info("Press Ctrl+C to stop")
                with VoiceSegmentStream(config, device=device) as stream:
                    for audio, start_time, end_time in stream.iter_segments():
                        whisper_start = time.time()
                        result = engine.transcribe(audio, language_hint=config.language)
                        whisper_end = time.time()

                        reference = parser.parse(result.text)
                        resolved_reference = sermon_context.process_input(result.text, reference)
                        parser_end = time.time()

                        if resolved_reference is not None:
                            if resolved_reference.canonical != last_reference:
                                last_reference = resolved_reference.canonical
                                logger.info("Detected Bible Reference: %s", resolved_reference.canonical)
                                if freeshow is not None:
                                    freeshow.send_reference(
                                        resolved_reference,
                                        start_time,
                                        end_time,
                                        whisper_start,
                                        whisper_end,
                                        parser_end
                                    )
                                else:
                                    # Print timings in dry run mode
                                    speech_duration = end_time - start_time
                                    whisper_latency = whisper_end - whisper_start
                                    parser_latency = parser_end - whisper_end
                                    total_latency = parser_end - end_time
                                    print(f"Speech duration: {speech_duration:.2f} s")
                                    print(f"Whisper: {whisper_latency:.2f} s")
                                    print(f"Parser: {parser_latency * 1000:.0f} ms")
                                    print(f"HTTP: 0 ms (Dry Run)")
                                    print(f"Total: {total_latency:.2f} s")
                                    print(f"Total latency: {total_latency:.2f} s")
                                    print(f"Whisper latency: {whisper_latency:.2f} s")
                            continue

                        if not result.text:
                            continue

                        if result.language is not None:
                            logger.info("Detected language: %s", result.language)
                        if result.average_confidence is not None:
                            logger.info("Average confidence: %.2f", result.average_confidence)
                        logger.info("Heard: %s", result.text)
                break
            except sd.PortAudioError as exc:
                print(f"PortAudio error: {exc}")
                if args.mic is not None:
                    return 1
                print("Choose another microphone.")
    except KeyboardInterrupt:
        logger.info("Stopping")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())