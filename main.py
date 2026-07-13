from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
import sounddevice as sd

from config import load_config
from freeshow import FreeShowClient
from mic import MicrophoneSelector, RecordingDevice, VoiceSegmentStream
from utils import setup_logging
from auto_advance import AutoAdvance
from speech_engine import SpeechEngine, GoogleSpeechEngine
from sermon_context import SermonContext
from intent_detector import IntentDetector
from bible_search import BibleSearch
from parser import BibleReference
from session import SermonSession, SCOPE_RESET_TIMEOUT
from reference_builder import ReferenceBuilder





def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice-to-Bible-reference transcription")
    parser.add_argument("--list-mics", action="store_true", help="List available microphones and exit")
    parser.add_argument("--mic", type=int, help="Microphone index from the listed devices")
    parser.add_argument("--model", help="Override the Faster-Whisper model size")
    parser.add_argument("--mode", choices=["FAST", "BALANCED", "ACCURATE", "fast", "balanced", "accurate"], help="Whisper latency mode")
    parser.add_argument("--language", choices=["AUTO", "ENGLISH", "TELUGU", "auto", "english", "telugu"], default="AUTO", help="Language mode (AUTO, ENGLISH, TELUGU)")
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

    engine: SpeechEngine = GoogleSpeechEngine(config)
    freeshow = FreeShowClient(config) if not args.dry_run else None
    sermon_context = SermonContext()
    intent_detector = IntentDetector()
    bible_search = BibleSearch()

    from correction_engine import CorrectionEngine
    correction_engine = CorrectionEngine()

    session = SermonSession()
    builder = ReferenceBuilder(timeout_seconds=config.reference_builder_timeout)

    shutdown_flag = False

    def _handle_sigterm(signum: int, frame) -> None:
        nonlocal shutdown_flag
        if shutdown_flag:
            sys.exit(128 + signum)
        shutdown_flag = True
        logger.info("SIGTERM received — shutting down")

    signal.signal(signal.SIGTERM, _handle_sigterm)

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
                    for item in stream.iter_segments():
                        if item is None:
                            now = time.time()
                            # Chapter-only ref: send after silence timeout if no verse arrived
                            if builder.book and builder.chapter and builder.verse is None and not builder.is_complete():
                                if now - builder.last_reference_time > config.chapter_silence_timeout:
                                    ref = builder.current_reference()
                                    if ref and ref.canonical != session.last_reference:
                                        session.last_reference = ref.canonical
                                        logger.info("Sending chapter-only ref after timeout: %s", ref.canonical)
                                        if freeshow is not None:
                                            freeshow.send_reference(ref, 0, 0, 0, 0, now)
                            # Reset search scope if no speech for a long time
                            if session.search_scope and (now - session.last_search_time) > SCOPE_RESET_TIMEOUT:
                                logger.info("Resetting search scope (timeout)")
                                session.search_scope = None
                                session.text_buffer = ""
                            continue

                        audio, start_time, end_time = item
                        whisper_start = time.time()
                        result = engine.transcribe(audio, language_hint=config.language)
                        if not result.text.strip():
                            result = engine.transcribe(audio, language_hint=config.language)
                        whisper_end = time.time()

                        if not result.text.strip():
                            continue

                        # Reactive auto-advance: advance only AFTER reader finishes a verse
                        if session.auto_advance and session.auto_advance.ready and session.last_speech_end is not None:
                            new_ref = session.auto_advance.process_advance(start_time, session.last_speech_end)
                            if new_ref:
                                logger.info("Auto-advance to: %s", new_ref.canonical)
                                if freeshow is not None:
                                    freeshow.send_reference(new_ref, start_time, end_time, whisper_start, whisper_end, time.time())
                                if session.auto_advance.finished:
                                    logger.info("Auto-advance finished range")
                                    session.auto_advance = None
                                session.last_speech_end = whisper_end
                                continue

                        session.last_speech_end = whisper_end

                        if session.auto_advance:
                            session.auto_advance.update_counters(end_time - start_time)

                        logger.info("Heard raw: %s", result.text)
                        if result.language is not None:
                            logger.info("Detected language: %s", result.language)
                        if result.average_confidence is not None:
                            logger.info("Average confidence: %.2f", result.average_confidence)

                        t_corr = t_intent = t_bible = t_sermon = t_freeshow = 0.0
                        t_start = time.time()

                        try:
                            _t = time.time()
                            corrected_text = correction_engine.process_utterance(result.text)
                            t_corr = time.time() - _t
                            logger.info("Heard corrected: %s", corrected_text)

                            _t = time.time()
                            intent, confidence = intent_detector.detect(corrected_text)
                            t_intent = time.time() - _t

                            logger.info("Intent = %s | Confidence = %.2f", intent, confidence)

                            # Auto Bible text matching (only if speech might be Bible-related)
                            session.text_buffer += corrected_text + " "
                            if len(session.text_buffer) > config.buffer_max_chars:
                                session.text_buffer = session.text_buffer[-config.buffer_max_chars:]
                            session.last_search_time = time.time()

                            query = session.text_buffer.strip()
                            min_len = config.full_text_min_len if session.search_scope is None else config.scope_text_min_len
                            min_score = config.text_match_score_scoped if session.search_scope else config.text_match_score_full
                            bible_match = None
                            _t = time.time()
                            should_search = intent != "IGNORE" or bible_search.might_be_bible(query)
                            if len(query) >= min_len and should_search:
                                bible_match = bible_search.search_best(query, search_scope=session.search_scope, min_score=min_score)
                            t_bible = time.time() - _t

                            if bible_match and bible_match.score >= min_score:
                                if session.search_scope is None:
                                    # Full-Bible search: require 2/3 consensus to avoid false positives
                                    session.match_history.append((bible_match.book, bible_match.chapter))
                                    if len(session.match_history) > 3:
                                        session.match_history.pop(0)
                                    same = sum(1 for bk, ch in session.match_history
                                               if bk == bible_match.book and ch == bible_match.chapter)
                                    if same < 2:
                                        bible_match = None
                                # Scoped: trust single match (already narrowed)
                            else:
                                # Reset consensus on no-match segments
                                session.match_history.clear()

                            if bible_match:
                                matched_ref = BibleReference(
                                    canonical=f"{bible_match.book} {bible_match.chapter}:{bible_match.verse}",
                                    book=bible_match.book,
                                    chapter=bible_match.chapter,
                                    verse=bible_match.verse,
                                )
                                if matched_ref.canonical != session.last_reference:
                                    session.last_reference = matched_ref.canonical
                                    logger.info("TEXT MATCH: %s %d:%d (score=%.0f)", bible_match.book, bible_match.chapter, bible_match.verse, bible_match.score)
                                    session.search_scope = (bible_match.book, bible_match.chapter)
                                    session.match_history.clear()
                                    session.auto_advance = AutoAdvance(matched_ref.book, matched_ref.chapter, matched_ref.verse, matched_ref.end_verse or 999)
                                    _t = time.time()
                                    if freeshow is not None:
                                        freeshow.send_reference(matched_ref, start_time, end_time, whisper_start, whisper_end, time.time())
                                    t_freeshow += time.time() - _t

                            # Feed into ReferenceBuilder (filler-tolerant)
                            builder.check_timeout()
                            builder.process(corrected_text)

                            # Use builder state to narrow BibleSearch scope
                            if builder.book and builder.chapter and session.search_scope is None:
                                session.search_scope = (builder.book, builder.chapter)

                            if confidence < config.min_confidence:
                                continue

                            if intent == "IGNORE":
                                continue

                            if intent not in ("REFERENCE", "CROSS_REFERENCE", "NAVIGATION"):
                                continue

                            if intent == "NAVIGATION":
                                _t = time.time()
                                resolved_reference = sermon_context.process_input(corrected_text, None)
                                t_sermon += time.time() - _t
                                parser_end = time.time()
                                if resolved_reference is not None and resolved_reference.canonical != session.last_reference:
                                    session.last_reference = resolved_reference.canonical
                                    logger.info("Navigation: %s", resolved_reference.canonical)
                                    if freeshow is not None:
                                        freeshow.send_reference(resolved_reference, start_time, end_time, whisper_start, whisper_end, parser_end)
                                    t_freeshow += time.time() - _t
                                continue

                            # REFERENCE / CROSS_REFERENCE — check builder completion
                            if not builder.is_complete():
                                continue

                            ref = builder.current_reference()
                            if ref is None or ref.canonical == session.last_reference:
                                builder.consume()
                                continue

                            session.last_reference = ref.canonical
                            logger.info("DETECTED REFERENCE: %s", ref.canonical)

                            if ref.verse is not None:
                                session.auto_advance = AutoAdvance(ref.book, ref.chapter, ref.verse, ref.end_verse or 999)
                                logger.info("Auto-advance started: %s %d:%d%s",
                                    session.auto_advance.book, session.auto_advance.chapter,
                                    session.auto_advance.current_verse,
                                    f"-{ref.end_verse}" if ref.end_verse else "+")

                            _t = time.time()
                            resolved_reference = sermon_context.process_input(corrected_text, ref)
                            t_sermon += time.time() - _t
                            parser_end = time.time()

                            if freeshow is not None:
                                freeshow.send_reference(resolved_reference or ref, start_time, end_time, whisper_start, whisper_end, parser_end)
                            t_freeshow += time.time() - _t

                            builder.consume()
                            continue
                        except Exception as exc:
                            logger.error("Error processing utterance: %s", exc, exc_info=True)
                        finally:
                            total = time.time() - t_start
                            logger.info(
                                "Latency: SR=%dms Corr=%dms Intent=%dms Bible=%dms Ctx=%dms FS=%dms Total=%dms",
                                (whisper_end - whisper_start) * 1000,
                                t_corr * 1000, t_intent * 1000, t_bible * 1000,
                                t_sermon * 1000, t_freeshow * 1000, total * 1000,
                            )
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