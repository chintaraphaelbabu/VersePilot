from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import warnings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import scipy.io.wavfile
import scipy.signal

warnings.filterwarnings("ignore", category=scipy.io.wavfile.WavFileWarning)

from versepilot.auto_advance import AutoAdvance
from versepilot.bible_search import BibleSearch
from versepilot.config import AppConfig, load_config, normalize_language_option
from versepilot.correction_engine import CorrectionEngine
from versepilot.intent_detector import IntentDetector
from versepilot.parser import BibleReference
from versepilot.reference_builder import ReferenceBuilder
from versepilot.candidate_engine import CandidateEngine
from versepilot.sermon_context import SermonContext
from versepilot.session import SermonSession, SCOPE_RESET_TIMEOUT
from versepilot.speech_engine import LocalWhisperEngine

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
CHUNK_SECONDS = 30
CHUNK_OVERLAP = 2
MIN_CHUNK_SAMPLES = 8000

logger = logging.getLogger("replay")
_BIBLE_SEARCH: BibleSearch | None = None


def get_bible_search() -> BibleSearch:
    global _BIBLE_SEARCH
    if _BIBLE_SEARCH is None:
        logger.info("Loading Bible search index...")
        _BIBLE_SEARCH = BibleSearch()
        logger.info("Bible search index ready (%d verses)", len(_BIBLE_SEARCH._verses))
    return _BIBLE_SEARCH


@dataclass
class TimelineEntry:
    timestamp: float
    segment_index: int
    raw_transcript: str = ""
    corrected_transcript: str = ""
    detected_intent: str = ""
    intent_confidence: float = 0.0
    builder_state: str = ""
    builder_book: str | None = None
    builder_chapter: int | None = None
    builder_verse: int | None = None
    builder_end_verse: int | None = None
    builder_confidence: float = 0.0
    builder_completed: bool = False
    builder_timed_out: bool = False
    bible_search_query: str = ""
    bible_match_book: str | None = None
    bible_match_chapter: int | None = None
    bible_match_verse: int | None = None
    bible_match_score: float = 0.0
    bible_match_text: str = ""
    emitted_reference: str | None = None
    emitted_ref_book: str | None = None
    emitted_ref_chapter: int | None = None
    emitted_ref_verse: int | None = None
    latency_stt: float = 0.0
    latency_correction: float = 0.0
    latency_intent: float = 0.0
    latency_bible: float = 0.0
    latency_context: float = 0.0
    latency_total: float = 0.0
    candidate_log: str = ""
    error: str | None = None


@dataclass
class SttRecordingItem:
    timestamp: float
    raw_text: str
    corrected_text: str


@dataclass
class SermonResult:
    name: str
    duration_seconds: float
    segments: int
    timeline: list[TimelineEntry] = field(default_factory=list)
    references_detected: list[dict[str, Any]] = field(default_factory=list)
    bible_matches: list[dict[str, Any]] = field(default_factory=list)
    builder_completions: int = 0
    builder_resets: int = 0
    builder_timeouts: int = 0
    errors: list[str] = field(default_factory=list)
    low_confidence: list[str] = field(default_factory=list)
    failed_bible_matches: int = 0
    incomplete_references: list[str] = field(default_factory=list)
    duplicate_references: list[str] = field(default_factory=list)
    parser_failures: list[str] = field(default_factory=list)
    navigation_failures: list[str] = field(default_factory=list)
    slow_processors: list[float] = field(default_factory=list)
    pipeline_log: list[str] = field(default_factory=list)
    stt_recording: list[SttRecordingItem] = field(default_factory=list)


def load_audio(path: str) -> tuple[np.ndarray, int]:
    ext = Path(path).suffix.lower()
    if ext == ".wav":
        rate, data = scipy.io.wavfile.read(path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data.astype(np.float64) / 32767.0, rate
    if ext in (".mp3", ".flac", ".m4a"):
        return _load_via_ffmpeg(str(Path(path).resolve()))
    raise ValueError(f"Unsupported audio format: {ext}")


def _load_via_ffmpeg(path: str) -> tuple[np.ndarray, int]:
    cmd = [
        "ffmpeg", "-y", "-i", path,
        "-ac", "1", "-ar", "16000",
        "-f", "wav", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Install ffmpeg or convert audio to WAV.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed on {path}: {e.stderr.decode(errors='replace')[:200]}") from e

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(result.stdout)
        wav_path = f.name
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", scipy.io.wavfile.WavFileWarning)
            rate, data = scipy.io.wavfile.read(wav_path)
        data = data.astype(np.float64) / 32767.0
        return data, rate
    finally:
        os.unlink(wav_path)


def chunk_audio(data: np.ndarray, rate: int) -> list[np.ndarray]:
    chunk_samples = CHUNK_SECONDS * rate
    overlap_samples = CHUNK_OVERLAP * rate
    stride = chunk_samples - overlap_samples
    chunks: list[np.ndarray] = []
    start = 0
    while start < len(data):
        end = start + chunk_samples
        chunk = data[start:end]
        if len(chunk) >= MIN_CHUNK_SAMPLES:
            chunks.append(chunk)
        if end >= len(data):
            break
        start += stride
    return chunks


def _resample_to_16k(data: np.ndarray, orig_rate: int) -> np.ndarray:
    if orig_rate == 16000:
        return data
    target_len = int(len(data) * 16000 / orig_rate)
    return scipy.signal.resample(data, target_len)


def _sermon_name(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"[^a-zA-Z0-9_\-\u0C00-\u0C7F]", "_", stem)
    return stem or "unknown"


def _make_replay_dir(base: str, name: str) -> str:
    d = os.path.join(base, name)
    os.makedirs(d, exist_ok=True)
    return d


class MockFreeShow:
    def send_reference(self, ref: BibleReference, *args, **kwargs) -> None:
        pass


def _pipeline_log_block(
    idx: int,
    entry: TimelineEntry,
    prev_state: str,
    prev_book: str | None,
    prev_chapter: int | None,
    prev_verse: int | None,
    prev_end_verse: int | None,
    builder: ReferenceBuilder,
    session: SermonSession,
    freeshow_action: str,
) -> str:
    ts = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]
    lines = [
        "=" * 30,
        f"SEGMENT #{idx}",
        f"Timestamp: {ts}",
        "",
        "Raw STT:",
        f"  {entry.raw_transcript or '(empty)'}",
        "",
        "Corrected:",
        f"  {entry.corrected_transcript or '(empty)'}",
        "",
        f"Intent: {entry.detected_intent or 'N/A'}",
        f"Confidence: {entry.intent_confidence:.2f}",
        "",
        "Builder BEFORE:",
        f"  State: {prev_state}",
        f"  Book: {prev_book}",
        f"  Chapter: {prev_chapter}",
        f"  Verse: {prev_verse}",
        f"  EndVerse: {prev_end_verse}",
        "",
        "Builder AFTER:",
        f"  State: {entry.builder_state}",
        f"  Book: {entry.builder_book}",
        f"  Chapter: {entry.builder_chapter}",
        f"  Verse: {entry.builder_verse}",
        f"  EndVerse: {entry.builder_end_verse}",
        "",
    ]
    # BibleSearch observability
    if session.search_scope:
        lines.append(f"BibleSearch: Searching {session.search_scope[0]} {session.search_scope[1]}")
    else:
        lines.append("BibleSearch: Searching Full Bible")
    if entry.bible_match_book:
        lines.append(f"")
        lines.append(f"Result: Matched {entry.bible_match_book} {entry.bible_match_chapter}:{entry.bible_match_verse}")
        lines.append(f"Score: {entry.bible_match_score:.0f}")
    elif len(entry.bible_search_query) >= 20:
        lines.append(f"")
        lines.append("Result: No match")
    else:
        lines.append(f"")
        lines.append("Result: Skipped (query too short)")
    lines.append("")
    lines.append(f"FreeShow: {freeshow_action}")
    if entry.emitted_reference:
        lines.append(f"  Reference: {entry.emitted_reference}")
    if entry.error:
        lines.append(f"  Error: {entry.error}")
    lines.append("")
    lines.append("=" * 30)
    return "\n".join(lines)


def process_sermon(
    audio_path: str,
    config: AppConfig,
    replay_base: str,
    stt_recording: list[SttRecordingItem] | None = None,
) -> SermonResult:
    is_replay = stt_recording is not None
    name = _sermon_name(audio_path) if not is_replay else os.path.splitext(os.path.basename(audio_path))[0]
    out_dir = _make_replay_dir(replay_base, name)
    log_path = os.path.join(out_dir, "replay.log")

    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    replay_logger = logging.getLogger("replay.sermon")
    replay_logger.addHandler(fh)
    replay_logger.setLevel(logging.DEBUG)

    engine: LocalWhisperEngine | None = None
    if not is_replay:
        try:
            engine = LocalWhisperEngine(config)
        except Exception as e:
            replay_logger.error("Failed to init SpeechEngine: %s", e)

    correction_engine = CorrectionEngine()
    intent_detector = IntentDetector()
    bible_search = get_bible_search()
    session = SermonSession()
    builder = ReferenceBuilder(timeout_seconds=config.reference_builder_timeout)
    candidate_engine = CandidateEngine()
    sermon_context = SermonContext()
    freeshow = MockFreeShow()

    result = SermonResult(name=name, duration_seconds=0.0, segments=0,
                          stt_recording=[] if not is_replay else stt_recording)

    if is_replay:
        result.segments = len(stt_recording)
        result.duration_seconds = stt_recording[-1].timestamp if stt_recording else 0
        replay_logger.info("Replaying %d STT items", len(stt_recording))
        items: list = stt_recording
    else:
        replay_logger.info("Loading audio: %s", audio_path)
        data, rate = load_audio(audio_path)
        if rate != 16000:
            data = _resample_to_16k(data, rate)
        duration = len(data) / 16000
        result.duration_seconds = duration
        replay_logger.info("Duration: %.1fs (%.1f min)", duration, duration / 60)
        items = chunk_audio(data, 16000)
        result.segments = len(items)
        replay_logger.info("Processing %d chunks", len(items))

    for idx, src in enumerate(items):
        entry = TimelineEntry(timestamp=time.time(), segment_index=idx)
        t_start = time.time()
        freeshow_action = "Skipped"
        prev_state = "N/A"
        prev_book = None
        prev_chapter = None
        prev_verse = None
        prev_end_verse = None

        try:
            if is_replay:
                rec: SttRecordingItem = src
                entry.raw_transcript = rec.raw_text
                entry.corrected_transcript = rec.corrected_text
                corrected_text = rec.corrected_text
                entry.latency_stt = 0
                entry.latency_correction = 0
                if not corrected_text.strip():
                    entry.latency_total = time.time() - t_start
                    result.timeline.append(entry)
                    continue
            else:
                stt_start = time.time()
                if engine is None:
                    raise RuntimeError("SpeechEngine not initialized")
                trans_result = engine.transcribe(src, language_hint=config.language)
                entry.latency_stt = time.time() - stt_start
                entry.raw_transcript = trans_result.text

                if not trans_result.text.strip():
                    entry.latency_total = time.time() - t_start
                    result.timeline.append(entry)
                    continue

                replay_logger.info("Chunk %d raw: %s", idx, trans_result.text)

                corr_start = time.time()
                corrected_text = correction_engine.process_utterance(trans_result.text)
                entry.latency_correction = time.time() - corr_start
                entry.corrected_transcript = corrected_text
                replay_logger.info("Chunk %d corrected: %s", idx, corrected_text)

                result.stt_recording.append(SttRecordingItem(
                    timestamp=time.time() - t_start,
                    raw_text=trans_result.text,
                    corrected_text=corrected_text,
                ))

            intent_start = time.time()
            intent, confidence = intent_detector.detect(corrected_text)
            entry.latency_intent = time.time() - intent_start
            entry.detected_intent = intent
            entry.intent_confidence = confidence
            replay_logger.info("Chunk %d intent: %s (%.2f)", idx, intent, confidence)

            if confidence < config.min_confidence:
                result.low_confidence.append(corrected_text)

            session.text_buffer += corrected_text + " "
            if len(session.text_buffer) > config.buffer_max_chars:
                session.text_buffer = session.text_buffer[-config.buffer_max_chars:]
            session.last_search_time = time.time()

            query = builder.current_reference().canonical if builder.is_complete() and builder.verse is not None else session.text_buffer.strip()
            min_len = config.full_text_min_len if session.search_scope is None else config.scope_text_min_len
            min_score = config.text_match_score_scoped if session.search_scope else config.text_match_score_full
            bible_match = None

            bible_start = time.time()
            should_search = intent != "IGNORE" or bible_search.might_be_bible(query)
            entry.bible_search_query = query
            if len(query) >= min_len and should_search:
                bible_match = bible_search.search_best(
                    query, search_scope=session.search_scope, min_score=min_score,
                )
            entry.latency_bible = time.time() - bible_start

            if bible_match and bible_match.score >= min_score:
                if session.search_scope is None:
                    session.match_history.append((bible_match.book, bible_match.chapter))
                    if len(session.match_history) > 3:
                        session.match_history.pop(0)
                    same = sum(1 for bk, ch in session.match_history
                               if bk == bible_match.book and ch == bible_match.chapter)
                    if same < 2:
                        bible_match = None
            else:
                session.match_history.clear()

            if bible_match:
                entry.bible_match_book = bible_match.book
                entry.bible_match_chapter = bible_match.chapter
                entry.bible_match_verse = bible_match.verse
                entry.bible_match_score = bible_match.score
                entry.bible_match_text = bible_match.text
                candidate_engine.update_bible_score(bible_match, session.search_scope)

                matched_ref = BibleReference(
                    canonical=f"{bible_match.book} {bible_match.chapter}:{bible_match.verse}",
                    book=bible_match.book,
                    chapter=bible_match.chapter,
                    verse=bible_match.verse,
                )
                if matched_ref.canonical != session.last_reference:
                    session.last_reference = matched_ref.canonical
                    session.search_scope = (bible_match.book, bible_match.chapter)
                    session.match_history.clear()
                    session.auto_advance = AutoAdvance(
                        matched_ref.book, matched_ref.chapter,
                        matched_ref.verse, matched_ref.end_verse or 999,
                    )
                    freeshow.send_reference(matched_ref, 0, 0, 0, 0, time.time())
                    freeshow_action = "Sent"
                    entry.emitted_reference = matched_ref.canonical
                    entry.emitted_ref_book = matched_ref.book
                    entry.emitted_ref_chapter = matched_ref.chapter
                    entry.emitted_ref_verse = matched_ref.verse
                    replay_logger.info("TEXT MATCH: %s (score=%.0f)", matched_ref.canonical, bible_match.score)
                    result.bible_matches.append({
                        "reference": matched_ref.canonical,
                        "book": matched_ref.book,
                        "chapter": matched_ref.chapter,
                        "verse": matched_ref.verse,
                        "score": bible_match.score,
                        "text": bible_match.text,
                    })
            else:
                if len(query) >= min_len and should_search:
                    result.failed_bible_matches += 1

            # ── observability tracking ──
            freeshow_action = "Skipped"

            # ReferenceBuilder with timeout — detect via state change
            prev_state = builder.state.name
            prev_book = builder.book
            prev_chapter = builder.chapter
            prev_verse = builder.verse
            prev_end_verse = builder.end_verse
            did_timeout = False if is_replay else builder.check_timeout()
            if did_timeout:
                entry.builder_timed_out = True
                result.builder_timeouts += 1
                result.builder_resets += 1
                if prev_book is not None:
                    incomplete = f"{prev_book}"
                    if prev_chapter:
                        incomplete += f" {prev_chapter}"
                    if prev_verse:
                        incomplete += f":{prev_verse}"
                    result.incomplete_references.append(incomplete)
                replay_logger.info("BUILDER RESET: Timeout — accumulated: %s %s:%s (before reset)",
                                   prev_book, prev_chapter or "?", prev_verse or "?")

            if builder.book and builder.chapter and session.search_scope is None:
                session.search_scope = (builder.book, builder.chapter)

            builder.process(corrected_text)
            entry.builder_state = builder.state.name
            entry.builder_book = builder.book
            entry.builder_chapter = builder.chapter
            entry.builder_verse = builder.verse
            entry.builder_end_verse = builder.end_verse
            entry.builder_confidence = builder.confidence
            candidate_engine.update_from_builder(builder)

            # Detect new-book reset inside builder.process
            if (prev_state != "WAITING_BOOK" and
                prev_book is not None and
                builder.state.name == "WAITING_BOOK" and
                not did_timeout):
                result.builder_resets += 1
                replay_logger.info("BUILDER RESET: New Book — accumulated: %s %s:%s (before reset)",
                                   prev_book, prev_chapter or "?", prev_verse or "?")

            if builder.is_complete():
                entry.builder_completed = True
                ref = builder.current_reference()
                if ref and ref.canonical != session.last_reference:
                    result.builder_completions += 1
                    freeshow_action = "Sent"

                    if intent in ("REFERENCE", "CROSS_REFERENCE", "NAVIGATION"):
                        ctx_start = time.time()
                        resolved = sermon_context.process_input(corrected_text, ref)
                        entry.latency_context = time.time() - ctx_start
                        if resolved:
                            entry.emitted_reference = resolved.canonical
                            entry.emitted_ref_book = resolved.book
                            entry.emitted_ref_chapter = resolved.chapter
                            entry.emitted_ref_verse = resolved.verse
                            freeshow.send_reference(resolved, 0, 0, 0, 0, time.time())
                    else:
                        # ponytail: send raw ref for non-standard intents (IGNORE range extension)
                        entry.emitted_reference = ref.canonical
                        entry.emitted_ref_book = ref.book
                        entry.emitted_ref_chapter = ref.chapter
                        entry.emitted_ref_verse = ref.verse
                        freeshow.send_reference(ref, 0, 0, 0, 0, time.time())

                    ref_dict = {"canonical": ref.canonical, "book": ref.book, "chapter": ref.chapter, "verse": ref.verse, "end_verse": ref.end_verse}
                    existing = [r["canonical"] for r in result.references_detected]
                    if ref.canonical not in existing:
                        result.references_detected.append(ref_dict)
                        replay_logger.info("BUILDER REF: %s", ref.canonical)
                    else:
                        freeshow_action = "Duplicate"
                        result.duplicate_references.append(ref.canonical)
                        replay_logger.info("DUPLICATE REF: %s (skipped)", ref.canonical)
                    session.last_reference = ref.canonical
                    replay_logger.info("BUILDER REF: %s (kept state for range extension)", ref.canonical)

            # Chapter-only fallback: if builder has book+chapter but no verse,
            # emit chapter ref (mirrors production chapter_silence_timeout)
            if builder.state.name == "WAITING_VERSE" and builder.book and builder.chapter and builder.verse is None:
                ch_ref = builder.current_reference()
                if ch_ref and ch_ref.canonical != session.last_reference:
                    session.last_reference = ch_ref.canonical
                    entry.emitted_reference = ch_ref.canonical
                    entry.emitted_ref_book = ch_ref.book
                    entry.emitted_ref_chapter = ch_ref.chapter
                    ch_ref_dict = {"canonical": ch_ref.canonical, "book": ch_ref.book, "chapter": ch_ref.chapter, "verse": None, "end_verse": None}
                    existing = [r["canonical"] for r in result.references_detected]
                    if ch_ref.canonical not in existing:
                        result.references_detected.append(ch_ref_dict)
                    freeshow_action = "Sent"
                    replay_logger.info("CHAPTER REF: %s", ch_ref.canonical)
                else:
                    freeshow_action = "Duplicate"

            if intent in ("REFERENCE", "CROSS_REFERENCE", "NAVIGATION"):
                if intent == "NAVIGATION":
                    ctx_start = time.time()
                    resolved = sermon_context.process_input(corrected_text, None)
                    entry.latency_context = time.time() - ctx_start
                    if resolved and resolved.canonical != session.last_reference:
                        session.last_reference = resolved.canonical
                        entry.emitted_reference = resolved.canonical
                        entry.emitted_ref_book = resolved.book
                        entry.emitted_ref_chapter = resolved.chapter
                        entry.emitted_ref_verse = resolved.verse
                        if entry.emitted_reference and freeshow_action == "Skipped":
                            freeshow_action = "Sent"
                    elif resolved is None and intent == "NAVIGATION":
                        result.navigation_failures.append(corrected_text)

            # ── Candidate Engine cycle ──
            candidate_engine.new_cycle()
            entry.candidate_log = candidate_engine.log()

        except Exception as e:
            entry.error = str(e)
            result.errors.append(str(e))
            replay_logger.error("Chunk %d error: %s", idx, e, exc_info=True)

        total = time.time() - t_start
        entry.latency_total = total
        if total > 10.0:
            result.slow_processors.append(total)
        block = _pipeline_log_block(
            idx, entry, prev_state, prev_book, prev_chapter,
            prev_verse, prev_end_verse, builder, session, freeshow_action,
        )
        result.pipeline_log.append(block)
        replay_logger.info("OBSERVABILITY\n%s", block)
        result.timeline.append(entry)

    replay_logger.removeHandler(fh)
    fh.close()
    return result


def write_sermon_outputs(result: SermonResult, out_dir: str) -> None:
    with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        for e in result.timeline:
            if e.raw_transcript:
                f.write(e.raw_transcript + "\n")

    with open(os.path.join(out_dir, "corrected_transcript.txt"), "w", encoding="utf-8") as f:
        for e in result.timeline:
            if e.corrected_transcript:
                f.write(e.corrected_transcript + "\n")

    with open(os.path.join(out_dir, "detected_references.json"), "w", encoding="utf-8") as f:
        json.dump({
            "references_detected": result.references_detected,
            "builder_completions": result.builder_completions,
            "builder_resets": result.builder_resets,
            "builder_timeouts": result.builder_timeouts,
            "duplicate_references": result.duplicate_references,
            "incomplete_references": result.incomplete_references,
        }, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out_dir, "bible_matches.json"), "w", encoding="utf-8") as f:
        json.dump(result.bible_matches, f, indent=2, ensure_ascii=False)

    timeline_dicts = [asdict(e) for e in result.timeline]
    with open(os.path.join(out_dir, "timeline.json"), "w", encoding="utf-8") as f:
        json.dump(timeline_dicts, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out_dir, "statistics.json"), "w", encoding="utf-8") as f:
        stt_times = [e.latency_stt for e in result.timeline if e.latency_stt > 0]
        total_times = [e.latency_total for e in result.timeline if e.latency_total > 0]
        json.dump({
            "name": result.name,
            "duration_seconds": result.duration_seconds,
            "segments": result.segments,
            "references_detected": result.references_detected,
            "bible_matches_count": len(result.bible_matches),
            "builder_completions": result.builder_completions,
            "builder_resets": result.builder_resets,
            "builder_timeouts": result.builder_timeouts,
            "errors": len(result.errors),
            "low_confidence_count": len(result.low_confidence),
            "avg_stt_latency": round(sum(stt_times) / len(stt_times), 3) if stt_times else 0,
            "avg_total_latency": round(sum(total_times) / len(total_times), 3) if total_times else 0,
            "max_total_latency": round(max(total_times), 3) if total_times else 0,
        }, f, indent=2, ensure_ascii=False)

    with open(os.path.join(out_dir, "timings.json"), "w", encoding="utf-8") as f:
        timing_data = [{
            "segment": e.segment_index,
            "stt": round(e.latency_stt, 3),
            "correction": round(e.latency_correction, 3),
            "intent": round(e.latency_intent, 3),
            "bible": round(e.latency_bible, 3),
            "context": round(e.latency_context, 3),
            "total": round(e.latency_total, 3),
        } for e in result.timeline]
        json.dump(timing_data, f, indent=2)

    with open(os.path.join(out_dir, "pipeline.log"), "w", encoding="utf-8") as f:
        for block in result.pipeline_log:
            f.write(block + "\n")

    if result.stt_recording:
        with open(os.path.join(out_dir, "stt_recording.json"), "w", encoding="utf-8") as f:
            json.dump([asdict(item) for item in result.stt_recording], f, indent=2, ensure_ascii=False)


def build_failure_report(results: list[SermonResult]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for r in results:
        for e in r.timeline:
            if e.error:
                failures.append({
                    "sermon": r.name,
                    "segment": e.segment_index,
                    "type": "error",
                    "error": e.error,
                    "transcript": e.raw_transcript,
                })
        if r.low_confidence:
            for t in r.low_confidence:
                failures.append({
                    "sermon": r.name,
                    "type": "low_confidence",
                    "transcript": t,
                })
        if r.duplicate_references:
            for ref in r.duplicate_references:
                failures.append({
                    "sermon": r.name,
                    "type": "duplicate_reference",
                    "reference": ref,
                })
        if r.builder_timeouts > 0:
            failures.append({
                "sermon": r.name,
                "type": "builder_timeout",
                "count": r.builder_timeouts,
            })
        if r.incomplete_references:
            failures.append({
                "sermon": r.name,
                "type": "incomplete_reference",
                "count": len(r.incomplete_references),
                "references": r.incomplete_references,
            })
        if r.errors:
            failures.append({
                "sermon": r.name,
                "type": "parser_failure",
                "count": len(r.errors),
            })
        if r.failed_bible_matches > 0:
            failures.append({
                "sermon": r.name,
                "type": "failed_bible_match",
                "count": r.failed_bible_matches,
            })
        if r.navigation_failures:
            failures.append({
                "sermon": r.name,
                "type": "navigation_failure",
                "utterances": r.navigation_failures,
            })
        slow = [t for t in r.slow_processors if t > 10.0]
        if slow:
            failures.append({
                "sermon": r.name,
                "type": "unusually_long_processing",
                "count": len(slow),
                "max_seconds": round(max(slow), 2),
            })
    return {"failures": failures, "total_sermons": len(results)}


def build_summary(results: list[SermonResult], failure_report: dict) -> str:
    total_sermons = len(results)
    total_duration = sum(r.duration_seconds for r in results)
    total_refs = set()
    for r in results:
        for ref in r.references_detected:
            total_refs.add(ref["canonical"])
    total_bible_matches = sum(len(r.bible_matches) for r in results)
    total_builder_completions = sum(r.builder_completions for r in results)
    total_builder_resets = sum(r.builder_resets for r in results)

    stt_latencies = [e.latency_stt for r in results for e in r.timeline if e.latency_stt > 0]
    total_latencies = [e.latency_total for r in results for e in r.timeline if e.latency_total > 0]
    parser_latencies = [e.latency_context for r in results for e in r.timeline if e.latency_context > 0]

    parser_fails = Counter()
    all_fails: Counter[str] = Counter()
    for f in failure_report.get("failures", []):
        all_fails[f["type"]] += f.get("count", 1)
        if f["type"] == "parser_failure":
            parser_fails[f["sermon"]] += f.get("count", 1)

    unmatched: Counter[str] = Counter()
    for r in results:
        for e in r.timeline:
            if e.detected_intent not in ("IGNORE", "") and not e.emitted_reference and not e.error:
                unmatched[e.corrected_transcript or e.raw_transcript] += 1

    lines = [
        "# Sermon Replay Summary",
        "",
        f"- **Total sermons processed:** {total_sermons}",
        f"- **Total duration:** {total_duration:.1f}s ({total_duration/60:.1f} min)",
        f"- **References detected (unique):** {len(total_refs)}",
        f"- **Bible text matches:** {total_bible_matches}",
        f"- **Builder completions:** {total_builder_completions}",
        f"- **Builder resets:** {total_builder_resets}",
        "",
        "## Latency",
    ]
    if stt_latencies:
        lines.append(f"- **Average STT latency:** {sum(stt_latencies)/len(stt_latencies):.3f}s")
    if parser_latencies:
        lines.append(f"- **Average parser latency:** {sum(parser_latencies)/len(parser_latencies):.3f}s")
    if total_latencies:
        lines.append(f"- **Average total latency:** {sum(total_latencies)/len(total_latencies):.3f}s")

    lines.extend([
        "",
        "## Failures",
        f"- **Total failure types:** {sum(all_fails.values())}",
    ])
    for fail_type, count in all_fails.most_common():
        lines.append(f"  - {fail_type}: {count}")

    if parser_fails:
        lines.extend(["", "### Most common parser failures"])
        for sermon, count in parser_fails.most_common(5):
            lines.append(f"  - {sermon}: {count}")

    if unmatched:
        lines.extend(["", "### Most common unmatched utterances"])
        for text, count in unmatched.most_common(10):
            lines.append(f"  - \"{text[:80]}\": {count}")

    return "\n".join(lines)


def _diagnose_failure(e: "TimelineEntry", prev_e: "TimelineEntry | None") -> tuple[str, str]:
    if e.error:
        return "Parser rejected", f"Exception: {e.error}"
    if e.builder_timed_out:
        return "Builder timeout", "Builder had partial reference but timed out before completion"
    if e.builder_book is None:
        return "Book never detected", "No Bible book name was recognized in the utterance"
    if e.builder_chapter is None:
        return "Chapter missing", f"Book '{e.builder_book}' was detected but chapter number never arrived"
    if e.builder_verse is None and e.builder_state == "WAITING_VERSE":
        return "Verse missing", f"Book+chapter ({e.builder_book} {e.builder_chapter}) detected but verse never arrived"
    if e.builder_state not in ("COMPLETE", "WAITING_VERSE", "WAITING_RANGE_END"):
        return "Builder incomplete", f"Builder stopped at {e.builder_state} with book={e.builder_book} ch={e.builder_chapter}"
    if not e.bible_match_book and len(e.bible_search_query or "") >= 20:
        return "BibleSearch confidence too low", f"Query '{e.bible_search_query[:60]}...' searched but no match met threshold"
    if prev_e and prev_e.emitted_reference and e.corrected_transcript:
        if e.corrected_transcript == prev_e.corrected_transcript:
            return "FreeShow duplicate suppression", f"'{e.corrected_transcript[:50]}' was already emitted in segment #{prev_e.segment_index}"
    cr = e.corrected_transcript or ""
    rw = e.raw_transcript or ""
    if cr != rw and cr and rw:
        return "Correction modified utterance", f"Raw and corrected text differ — correction may have altered reference content"
    return "Unknown", "Root cause not determined from available data"


def build_failure_report_md(results: list[SermonResult]) -> str:
    sections: list[str] = ["# Failure Report", "",
                           "Auto-generated analysis of every missed reference.",
                           "A reference is 'missed' when the pipeline received non-IGNORE",
                           "utterance content but did not emit a reference to FreeShow.",
                           ""]
    failure_count = 0
    root_causes: Counter[str] = Counter()
    for r in results:
        prev_e: TimelineEntry | None = None
        for e in r.timeline:
            # If reference was emitted, it's not a failure
            if e.emitted_reference:
                prev_e = e
                continue
            # Missed reference = non-IGNORE utterance that should've produced a ref
            is_missed = (e.detected_intent not in ("IGNORE", "", None) and
                         not e.error)
            # Builder timeouts (partial refs that got stuck)
            is_timeout = e.builder_timed_out and e.detected_intent not in ("IGNORE", "", None)
            # Errors on non-IGNORE utterances
            is_error = bool(e.error) and e.detected_intent not in ("IGNORE", "", None)
            if not is_missed and not is_timeout and not is_error:
                prev_e = e
                continue
            failure_count += 1
            root_cause, detail = _diagnose_failure(e, prev_e)
            root_causes[root_cause] += 1
            raw = e.raw_transcript or "(empty)"
            corr = e.corrected_transcript or "(empty)"
            intent = f"{e.detected_intent} (confidence: {e.intent_confidence:.2f})"
            bstate = f"{e.builder_state} | book={e.builder_book} ch={e.builder_chapter} v={e.builder_verse} end={e.builder_end_verse}"
            if e.bible_match_book:
                bsearch = f"Matched {e.bible_match_book} {e.bible_match_chapter}:{e.bible_match_verse} score={e.bible_match_score:.0f}"
            elif len(e.bible_search_query or "") >= 20:
                bsearch = f"Searched (query: {e.bible_search_query[:60]}...) — no match"
            else:
                bsearch = "Skipped (query too short or intent IGNORE)"
            freeshow = f"{'Sent: ' + e.emitted_reference if e.emitted_reference else 'Nothing sent'}"
            sections.extend([
                f"## Failure #{failure_count} (sermon: {r.name}, segment: {e.segment_index})",
                "",
                f"**Raw STT:** {raw}",
                "",
                f"**Corrected:** {corr}",
                "",
                f"**Intent:** {intent}",
                "",
                f"**Builder state:** {bstate}",
                "",
                f"**BibleSearch:** {bsearch}",
                "",
                f"**FreeShow:** {freeshow}",
                "",
                f"**Root cause:** {root_cause}",
                "",
                f"**Detail:** {detail}",
                "",
                "---",
                "",
            ])
    if failure_count == 0:
        sections.append("No missed references found.")
    else:
        sections.extend(["", "## Root Cause Summary", ""])
        for cause, count in root_causes.most_common():
            sections.append(f"- **{cause}**: {count}")
        sections.append("")
    sections.append(f"_Total failures analyzed: {failure_count}_")
    return "\n".join(sections)


def build_corpus_additions(results: list[SermonResult]) -> str:
    seen_refs: dict[str, dict[str, Any]] = {}
    for r in results:
        for ref in r.references_detected:
            seen_refs[ref["canonical"]] = ref

    distinct_utterances: set[str] = set()
    for r in results:
        for e in r.timeline:
            if e.corrected_transcript and e.corrected_transcript != e.raw_transcript:
                distinct_utterances.add(e.corrected_transcript)

    lines = [
        "# Proposed church_corpus_additions.yaml",
        "# Auto-generated from sermon replay results",
        "# Review and manually merge into church_corpus.yaml",
        "",
        f"# {len(seen_refs)} unique references detected across {len(results)} sermons",
        "",
        "entries:",
    ]

    for ref_str in sorted(seen_refs):
        ref = seen_refs[ref_str]
        lines.append(f"  - reference: \"{ref_str}\"")
        lines.append(f"    book: \"{ref['book']}\"")
        if ref.get("chapter"):
            lines.append(f"    chapter: {ref['chapter']}")
        if ref.get("verse"):
            lines.append(f"    verse: {ref['verse']}")
        if ref.get("end_verse"):
            lines.append(f"    end_verse: {ref['end_verse']}")
        lines.append("")

    lines.append(f"# {len(distinct_utterances)} distinct corrected utterances observed")
    lines.append("# candidate_corpus_utterances:")
    for utt in sorted(distinct_utterances):
        if len(utt) < 120:
            lines.append(f"#   - \"{utt}\"")

    return "\n".join(lines)


_ROOT_CAUSE_LABELS = {
    "romanized_alias": "Romanized Alias",
    "missing_filler": "Missing Filler",
    "bible_search": "BibleSearch",
    "correction": "Correction",
    "navigation": "Navigation",
    "builder_timeout": "Builder Timeout",
    "other": "Other",
}

_ROOT_CAUSE_FIXES = {
    "romanized_alias": "Add missing romanized alias to `normalizer.py` `ROMANIZED_LOOKUP` dict, or add spoken variant to `books.py` `spoken_variants`.",
    "missing_filler": "Add utterance to `church_corpus.yaml` so `might_be_bible()` detects it as Bible-related content.",
    "bible_search": "Lower `text_match_score_*` threshold in config, or ensure query contains distinctive Bible keywords.",
    "correction": "Review `correction_engine.py` repair logic — correction may be stripping valid reference content.",
    "navigation": "Add missing navigation phrase pattern to `sermon_context.py` `parse_voice_command()`.",
    "builder_timeout": "Increase `reference_builder_timeout` in config, or add book/chapter/verse spoken variants to `books.py`.",
    "other": "Inspect individual failure details in `failure_report.md`.",
}


def _classify_root_cause(
    e: TimelineEntry,
    prev_e: TimelineEntry | None,
    result: SermonResult,
) -> str:
    cr = e.corrected_transcript or ""
    rw = e.raw_transcript or ""
    if e.builder_timed_out:
        return "builder_timeout"
    if e.detected_intent == "NAVIGATION" and not e.emitted_reference:
        return "navigation"
    if cr and rw and cr != rw:
        return "correction"
    if e.builder_book is None and not e.bible_match_book:
        return "missing_filler"
    if e.builder_book is not None and e.builder_chapter is None:
        return "missing_filler"
    if e.builder_book is not None and e.builder_verse is None and e.builder_state == "WAITING_VERSE":
        return "builder_timeout"
    if not e.bible_match_book and len(e.bible_search_query or "") >= 20:
        return "bible_search"
    if len(e.bible_search_query or "") < 20:
        return "missing_filler"
    return "other"


def build_learning_report(results: list[SermonResult]) -> str:
    groups: dict[str, list[dict]] = {k: [] for k in _ROOT_CAUSE_LABELS}
    for r in results:
        prev_e: TimelineEntry | None = None
        for e in r.timeline:
            if e.emitted_reference:
                prev_e = e
                continue
            is_missed = (e.detected_intent not in ("IGNORE", "", None) and not e.error)
            is_timeout = e.builder_timed_out and e.detected_intent not in ("IGNORE", "", None)
            is_error = bool(e.error) and e.detected_intent not in ("IGNORE", "", None)
            if not is_missed and not is_timeout and not is_error:
                prev_e = e
                continue
            key = _classify_root_cause(e, prev_e, r)
            groups.setdefault(key, []).append({
                "sermon": r.name,
                "segment": e.segment_index,
                "raw": e.raw_transcript,
                "corrected": e.corrected_transcript,
                "intent": e.detected_intent,
                "builder_state": e.builder_state,
                "bible_query": e.bible_search_query,
                "bible_match": f"{e.bible_match_book} {e.bible_match_chapter}:{e.bible_match_verse}" if e.bible_match_book else None,
                "emitted": e.emitted_reference,
                "error": e.error,
            })
            prev_e = e

    sections: list[str] = [
        "# Learning Report",
        "",
        "Auto-generated root-cause analysis aggregated across all processed sermons.",
        "Each failure is classified into one root-cause bucket for prioritized fixing.",
        "",
    ]

    total_failures = sum(len(v) for v in groups.values())
    sections.append(f"_Total failures analyzed: {total_failures}_")
    sections.append("")

    for key in _ROOT_CAUSE_LABELS:
        items = groups.get(key, [])
        if not items:
            continue
        label = _ROOT_CAUSE_LABELS[key]
        sermons_affected = len(set(it["sermon"] for it in items))
        freq_pct = len(items) / total_failures * 100 if total_failures else 0
        confidence = round(1.0 - (0.1 * len(set(it["sermon"] for it in items)) / max(len(results), 1)), 2)
        confidence = max(0.50, min(0.99, confidence))

        example_utterances = []
        seen = set()
        for it in items:
            utt = it["corrected"] or it["raw"] or ""
            if utt not in seen and len(utt) > 2:
                example_utterances.append(utt)
                seen.add(utt)
                if len(example_utterances) >= 5:
                    break

        sections.extend([
            f"## {label}",
            "",
            f"- **Frequency:** {len(items)} occurrences across {sermons_affected} sermon(s) ({freq_pct:.0f}% of all failures)",
            f"- **Confidence:** {confidence:.2f}",
            "",
            "### Example Utterances",
            "",
        ])
        for utt in example_utterances:
            sections.append(f"- `{utt[:100]}`")
        sections.extend([
            "",
            "### Suggested Fix",
            "",
            _ROOT_CAUSE_FIXES.get(key, ""),
            "",
            "---",
            "",
        ])

    sections.append("_End of report._")
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verses Sermon Replay & Evaluation Framework",
    )
    parser.add_argument(
        "--dataset", default="sermon_files/video",
        help="Directory containing sermon audio files (default: sermon_files/video/)",
    )
    parser.add_argument(
        "--replay-dir", default="outputs/replay",
        help="Output directory for replay artifacts (default: outputs/replay/)",
    )
    parser.add_argument(
        "--language", choices=["auto", "english", "telugu"], default="auto",
        help="Language hint for STT (default: auto)",
    )
    parser.add_argument(
        "--chunk-seconds", type=int, default=30,
        help="Audio chunk size in seconds (default: 30)",
    )
    parser.add_argument(
        "--chunk-overlap", type=float, default=2.0,
        help="Overlap between chunks in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--stt-recording",
        help="Replay from saved STT recording JSON instead of processing audio",
    )
    args = parser.parse_args()

    global CHUNK_SECONDS, CHUNK_OVERLAP
    CHUNK_SECONDS = args.chunk_seconds
    CHUNK_OVERLAP = int(args.chunk_overlap)

    config = load_config()
    if args.language:
        config.language = normalize_language_option(args.language)

    os.makedirs(args.replay_dir, exist_ok=True)

    results: list[SermonResult] = []

    if args.stt_recording:
        # ── replay mode: load saved STT, skip audio processing ──
        stt_path = args.stt_recording
        if not os.path.isfile(stt_path):
            print(f"ERROR: STT recording not found: {stt_path}")
            return 1
        with open(stt_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        recording = [SttRecordingItem(**item) for item in raw]
        name = Path(stt_path).stem.replace("_stt_recording", "")
        print(f"Replaying {name} ({len(recording)} items)...", end=" ", flush=True)
        try:
            result = process_sermon(stt_path, config, args.replay_dir, stt_recording=recording)
            out_dir = os.path.join(args.replay_dir, name)
            write_sermon_outputs(result, out_dir)
            results.append(result)
            print(f"OK ({result.segments} segments)")
        except Exception as e:
            print(f"FAILED: {e}")
            logger.error("Failed to replay %s: %s", stt_path, e, exc_info=True)
    else:
        # ── record mode: process audio files with Google STT ──
        dataset_dir = args.dataset
        if not os.path.isdir(dataset_dir):
            print(f"ERROR: dataset directory not found: {dataset_dir}")
            return 1

        audio_files = []
        for f in sorted(os.listdir(dataset_dir)):
            ext = Path(f).suffix.lower()
            if ext in AUDIO_EXTENSIONS:
                audio_files.append(os.path.join(dataset_dir, f))

        if not audio_files:
            print(f"No audio files found in {dataset_dir} (supported: {', '.join(AUDIO_EXTENSIONS)})")
            return 1

        print(f"Found {len(audio_files)} audio files in {dataset_dir}/")
        print(f"Output: {args.replay_dir}/")

        for idx, audio_path in enumerate(audio_files):
            name = _sermon_name(audio_path)
            print(f"[{idx + 1}/{len(audio_files)}] {name}...", end=" ", flush=True)
            try:
                result = process_sermon(audio_path, config, args.replay_dir)
                out_dir = os.path.join(args.replay_dir, name)
                write_sermon_outputs(result, out_dir)
                results.append(result)
                print(f"OK ({result.segments} chunks, {result.duration_seconds:.0f}s)")
            except Exception as e:
                print(f"FAILED: {e}")
                logger.error("Failed to process %s: %s", audio_path, e, exc_info=True)

    print()
    print("=" * 60)
    print("GENERATING REPORTS")
    print("=" * 60)

    failure_report = build_failure_report(results)
    with open(os.path.join(args.replay_dir, "failure_report.json"), "w", encoding="utf-8") as f:
        json.dump(failure_report, f, indent=2, ensure_ascii=False)
    print(f"  failure_report.json ({len(failure_report['failures'])} issues)")

    summary = build_summary(results, failure_report)
    with open(os.path.join(args.replay_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"  summary.md ({len(results)} sermons)")

    failure_md = build_failure_report_md(results)
    with open(os.path.join(args.replay_dir, "failure_report.md"), "w", encoding="utf-8") as f:
        f.write(failure_md)
    print(f"  failure_report.md")

    corpus = build_corpus_additions(results)
    with open(os.path.join(args.replay_dir, "church_corpus_additions.yaml"), "w", encoding="utf-8") as f:
        f.write(corpus)
    print("  church_corpus_additions.yaml")

    learning = build_learning_report(results)
    with open(os.path.join(args.replay_dir, "learning_report.md"), "w", encoding="utf-8") as f:
        f.write(learning)
    print("  learning_report.md")

    print()
    for line in summary.split("\n")[1:6]:
        if line.startswith("-"):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
