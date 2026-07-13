# Verses — Technical Documentation

## Overview

Verses listens to a church audio feed, transcribes Telugu/English speech via Google Speech-to-Text, extracts Bible references (e.g. "కీర్తనలు 25:14" or "aadikaandamu 1 1"), and sends them to FreeShow for display. It also has auto-Bible-text-matching: when the reader recites verse text, the system fuzzy-matches against a local Telugu Bible database to identify the reference. A ReferenceBuilder state machine accumulates reference info across utterances, tolerating filler words like "మనమందరము" and "తెరిచినట్లయితే".

---

## File Structure

```
verses/
  main.py                — Entry point, main loop, audio capture, flow orchestration
  reference_builder.py   — State machine for cross-utterance reference accumulation
  bible_search.py        — Telugu Bible fuzzy search engine (rapidfuzz)
  mic.py                 — Microphone selection, VAD, audio segmentation
  speech_engine.py       — Abstract SpeechEngine base + GoogleSpeechEngine (Google STT)
  session.py             — SermonSession dataclass, shared state
  parser.py              — BibleReference dataclass + BibleReferenceParser (fallback)
  normalizer.py          — Telugu reference normalizer, book alias maps, ROMANIZED_LOOKUP
  correction_engine.py   — Utterance correction with book/number extraction
  intent_detector.py     — Classifies speech as REFERENCE, NAVIGATION, IGNORE, CROSS_REFERENCE
  sermon_context.py      — Tracks context state (current passage, navigation)
  freeshow.py            — Async HTTP client for FreeShow API (port 5506)
  config.py              — AppConfig dataclass + env-var loading
  utils.py               — Logging setup
  books.py               — All 66 Bible book entries with Telugu/English aliases
  book_ids.py            — Book name → FreeShow numeric ID mapping
  spoken_numbers.py      — Telugu/English number word → digit normalization
  telugu_bible.json      — 31,101 Telugu Bible (BSI) verses in JSON format
  auto_advance.py        — Auto-advance logic for verse ranges
  church_corpus.yaml     — 488 sermon utterance test cases
  test_parser.py         — 308 normalizer + parser + intent unit tests
  test_corpus.py         — Validates church_corpus.yaml against parser
  test_reference_builder.py — 13 ReferenceBuilder state machine tests
  test_e2e.py            — 13 end-to-end pipeline tests with mocks
```

---

## Module-by-Module Breakdown

### `main.py`

The orchestrator. Runs the infinite event loop with VAD segmentation.

#### Configuration (all in `config.py`)

All tunable parameters are in `AppConfig`, loaded via `load_config()`. Env-var overrides listed below.

#### State Variables (in `SermonSession`)

| Variable | Type | Purpose |
|----------|------|---------|
| `last_reference` | `str \| None` | Canonical string of the last ref sent to FreeShow (dedup guard) |
| `auto_advance` | `AutoAdvance \| None` | Active auto-advance state (book, chapter, current_verse, end_verse) |
| `last_speech_end` | `float \| None` | Timestamp of when the last speech segment finished processing |
| `text_buffer` | `str` | Rolling buffer of recent corrected speech (capped at `buffer_max_chars`) |
| `search_scope` | `tuple[str, int] \| None` | Current BibleSearch scope `(book, chapter)` when chapter is known |
| `last_search_time` | `float` | Timestamp of last search (for `SCOPE_RESET_TIMEOUT`) |
| `match_history` | `list[tuple[str, int, float]]` | Last 3 match results for 2/3 consensus |

#### Main Loop Flow

```
for item in stream.iter_segments():
```

**Idle branch** (`item is None`, fires every ~500ms):
1. If `ReferenceBuilder` has book+chapter but no verse and 3s+ elapsed → send chapter-only ref to FreeShow
2. If `search_scope` is set and no speech for 60s → reset scope, clear buffer

**Speech branch** (`item` is `(audio, start_time, end_time)`):

1. **Transcribe** via `GoogleSpeechEngine.transcribe()` — Google STT, Telugu first, English fallback. Retries once on empty result.
2. **Auto-advance check** — If auto-advance is active and reader pauses 3s+ with enough segments → advance to next verse
3. **Correction** — Run `CorrectionEngine.process_utterance()` to detect/repair corrections
4. **Intent detection** — `IntentDetector.detect()` classifies speech as REFERENCE/NAVIGATION/CROSS_REFERENCE/IGNORE
5. **Bible text matching** — Append to `text_buffer`, search via `BibleSearch.search_best()`
   - Full-Bible search (no scope): require buffer `>= 20` chars and score `>= 85` with 2/3 consensus
   - Scoped search (chapter known): require `>= 12` chars and score `>= 50` (single match trusted)
   - On match: send to FreeShow, set `search_scope`, start auto-advance
6. **ReferenceBuilder** — Feed corrected text into `ReferenceBuilder.process()`. Builder is filler-tolerant; non-reference words never clear accumulated state. 20s timeout resets only if no reference info received.
7. **Builder narrows scope** — If builder has book+chapter and no search scope yet, narrow `BibleSearch` to that chapter
8. **Low-confidence filter** — If `confidence < config.min_confidence`, skip
9. **IGNORE** — Skip
10. **NAVIGATION** — Resolve via `SermonContext.process_input()`, send to FreeShow
11. **REFERENCE / CROSS_REFERENCE** — Check `builder.is_complete()`; if so, send to FreeShow, start auto-advance if verse present
12. **Error handling** — All internal processing wraps in try/except with `logger.error(exc_info=True)` to prevent crashes

---

### `reference_builder.py`

State machine that accumulates Bible reference info across utterances. Replaces the old per-utterance partial-ref combining.

#### States

| State | Meaning | Triggers |
|-------|---------|----------|
| `WAITING_BOOK` | Waiting for any book name | Any `BOOK` token transitions to WAITING_CHAPTER |
| `WAITING_CHAPTER` | Book known, waiting for chapter | `NUMBER` token → WAITING_VERSE |
| `WAITING_VERSE` | Chapter known, waiting for verse | `NUMBER` → set verse. If range indicator follows → WAITING_RANGE_END. If another number follows → COMPLETE (end_verse). Otherwise → COMPLETE |
| `WAITING_RANGE_END` | Verse known, waiting for end-verse | `NUMBER` → COMPLETE |
| `COMPLETE` | Full reference assembled | Ignores everything until new book or timeout |

#### Key Properties

- **Filler-tolerant**: IGNORE/UNKNOWN tokens never reset state. Only a new BOOK token causes a reset.
- **Range indicators**: నుండి/నుంచి/వరకు/దాకా/through/to/nundi/nunchi/varaku/- trigger WAITING_RANGE_END transition.
- **Timeout**: 20s (configurable) with no reference-related input → auto-reset.
- **Numbered books**: Stores `_pending_book_prefix` when a number precedes a book name (e.g. "1" then "Timothy" → "1 Timothy").
- **Telugu number formats**: Normalized via `normalize_spoken_numbers()` before tokenization.

---

### `bible_search.py`

Fuzzy search engine against 31,101 Telugu Bible verses using `rapidfuzz.fuzz.partial_ratio`.

#### Indexes

- `_verses: list[VerseInfo]` — All verses in order
- `_by_book_chapter: dict[(book, chapter), list[VerseInfo]]` — Chapter-scoped lookup
- `_by_chapter_verse: dict[(book, chapter, verse), VerseInfo]` — Direct verse lookup
- `_word_index: dict[str, set[int]]` — Word → verse-index set (O(1) `might_be_bible()`)
- `_ngram_index: dict[str, set[int]]` — 3-char ngram → verse-index set (candidate narrowing)

#### Search Flow

1. **`might_be_bible(text)`** — O(tokens) check: any token in word_index? Gates search CPU.
2. **`_get_candidates(query)`** — Union of word-index and ngram-index verse IDs. Returns None if too broad (>95% of verses).
3. **`search(query, search_scope, top_n, min_score)`** — If scope: filter to chapter (~30 verses). Else: use candidates or full Bible. Scores each via `partial_ratio`.
4. **`search_best(...)`** — Returns top-1 result.

---

### `mic.py`

Real-time voice activity detection (VAD) segmentation.

#### `VoiceSegmentStream`

Segmentation parameters (all from config):
- `frame_ms`: 30ms
- `padding_ms`: 150ms pre-roll
- `silence_ms`: 200ms silence to end segment
- `min_speech_ms`: 400ms minimum to emit
- `max_utterance_ms`: 60s max segment

**VAD**: Uses `webrtcvad` (aggressiveness 0 = most sensitive), falls back to `_EnergyVad` (threshold 0.006 RMS).

---

### `speech_engine.py`

`GoogleSpeechEngine` — Google Web Speech API STT.

1. Writes float32 audio to temp WAV
2. Calls `recognize_google(audio, language="te-IN")` (Telugu)
3. On empty/failure, falls back to `recognize_google(audio, language="en-US")`

**Caveat**: Requires internet. Free tier: 60 req/min. No local fallback.

---

### `normalizer.py`

Tokenization, classification, and book alias resolution.

#### Key Data Structures

| Name | Purpose |
|------|---------|
| `_SINGLE_BOOK_MAP` | All single-word aliases (Telugu + Romanized + English) → canonical book name |
| `_NUMBERED_BASE` | Base name → numbered variants dict (e.g. `"peter" → {1: "1 Peter", 2: "2 Peter"}`) |
| `ROMANIZED_LOOKUP` | 150+ Romanized Telugu transliterations (e.g. `"aadikaandamu" → "Genesis"`) |
| `IGNORE_WORDS` | Common filler words filtered from classification (Telugu + English + Romanized) |

#### Classification

`tokenize()` → `classify(tokens)`:
- `BOOK` — Matched via `_single_book_lookup()` with Telugu suffix stripping (-కు, -కి, -నకు, -ల)
- `NUMBER` — Digit or Telugu/English number word
- `CHAPTER` / `VERSE` — Chapter/verse marker words
- `CORRECTION` — "ఆ"/"aa" context-dependent: only when preceded by a number or standalone followed by a number
- `IGNORE` — Filler/noise words
- `UNKNOWN` — Everything else

---

### `correction_engine.py`

Extracts structured reference info from utterance. Stateless per utterance.

- Tokenizes with book alias substitution (longest-match first)
- Tracks `MutableBibleReference` fields as tokens are consumed
- Repair markers (sorry/కాదు/లేదు/అంటే/ఆ) trigger field re-assignment
- If no book found in utterance, returns original text unchanged (preserving range indicators for ReferenceBuilder)

---

### `intent_detector.py`

Classification pipeline with priority ordering to minimize false positives.

**`detect(text)`** → `(intent, confidence)`:
1. **Exact book match** via `_BOOK_REGEX` (built from all aliases + `_SINGLE_BOOK_MAP` bare names)
   - Cross-ref keywords → `CROSS_REFERENCE`
   - Book + number → `REFERENCE`
   - Book only → `IGNORE`
2. **Navigation regex** — English + Telugu patterns (next/prev verse/chapter, go back/forward, continue)
3. **Fuzzy book match** — `fuzz.partial_ratio ≥ 85` on remaining non-matched tokens

Cross-ref keywords: see also, compare, చూడండి, చూడు, పోల్చి, పోల్చుము.

Navigation patterns: next/previous verse/chapter, go back, continue, తరువాతి వచనం/అధ్యాయం, వెనక్కి వెళ్ళండి, ముందుకు వెళ్ళండి, తిరిగి వెళ్ళండి.

---

### `sermon_context.py`

Tracks current Bible passage and handles navigation commands.

**`process_input(text, reference)`**:
- If `reference` is provided → set as primary
- If `text` is a voice command → navigate relative to current context

---

### `freeshow.py`

Background-thread HTTP client for FreeShow API (port 5506).

**`_send_now()`**: POST `{"action": "start_scripture", "reference": "book_id.chapter.verse"}`

Uses a daemon thread with queue to avoid blocking the audio loop.

---

### `auto_advance.py`

Automatic verse progression when reader pauses between verses.

**`process_advance(start_time, last_speech_end)`**:
- Gap > 10s → reset counters (reader may have stopped)
- Gap > 3s AND (segments ≥ 3 OR speech ≥ 4s) → advance to next verse
- Returns `BibleReference` for the advanced verse, or `None`

---

### `config.py`

`AppConfig` dataclass with env-var overrides.

#### Fields

| Field | Default | Env | Purpose |
|-------|---------|-----|---------|
| `whisper_model_name` | (mode-based) | `VERSE_WHISPER_MODEL_NAME` | (unused, Google STT) |
| `device` | cpu | `VERSE_DEVICE` | (unused) |
| `compute_type` | int8 | `VERSE_COMPUTE_TYPE` | (unused) |
| `whisper_sample_rate` | 16000 | `VERSE_WHISPER_SAMPLE_RATE` | STT sample rate |
| `frame_ms` | 30 | `VERSE_FRAME_MS` | VAD frame size |
| `padding_ms` | 150 | `VERSE_PADDING_MS` | Pre-roll padding |
| `silence_ms` | 200 | `VERSE_SILENCE_MS` | Silence to end segment |
| `min_speech_ms` | 400 | `VERSE_MIN_SPEECH_MS` | Min speech segment |
| `max_utterance_ms` | 60000 | `VERSE_MAX_UTTERANCE_MS` | Max segment length |
| `log_level` | INFO | `VERSE_LOG_LEVEL` | Logging level |
| `language` | auto | `VERSE_LANGUAGE` | Language hint |
| `freeshow_host` | 127.0.0.1 | `FREESHOW_HOST` | FreeShow API host |
| `freeshow_port` | 5506 | `FREESHOW_PORT` | FreeShow API port |
| `whisper_mode` | BALANCED | `VERSE_WHISPER_MODE` | (unused) |
| `reference_builder_timeout` | 20 | `VERSE_BUILDER_TIMEOUT` | Builder idle timeout (s) |
| `chapter_silence_timeout` | 3.0 | `VERSE_CHAPTER_TIMEOUT` | Silence before chapter-only send (s) |
| `min_confidence` | 0.80 | `VERSE_MIN_CONFIDENCE` | Minimum intent confidence |
| `text_match_score_full` | 85 | `VERSE_TEXT_MATCH_FULL` | Full-Bible match threshold |
| `text_match_score_scoped` | 50 | `VERSE_TEXT_MATCH_SCOPED` | Scoped match threshold |
| `buffer_max_chars` | 300 | `VERSE_BUFFER_MAX` | Text buffer cap |
| `scope_text_min_len` | 12 | `VERSE_SCOPE_MIN_LEN` | Min chars for scoped search |
| `full_text_min_len` | 20 | `VERSE_FULL_MIN_LEN` | Min chars for full search |

---

### `books.py`

All 66 Bible books as `BookEntry(canonical, aliases_tuple)`. Aliases include:
- English abbreviations (gen, ex, lev, num, deut...)
- Telugu full names (ఆదికాండము, నిర్గమకాండము...)
- Common Telugu short forms (ఆది, నిర్గమ...)

---

### `session.py`

Minimal shared state: `SermonSession` dataclass with `last_reference`, `auto_advance`, `last_speech_end`, `text_buffer`, `search_scope`, `last_search_time`, `match_history`.

Constants:
- `SCOPE_RESET_TIMEOUT = 60.0` — seconds of silence before search scope resets

---

## Data Flow Diagram

```
Audio (church feed)
  → VoiceSegmentStream (VAD segmentation)
    → None (idle): check builder chapter-only timeout, check scope reset
    → (audio, start, end):
        1. GoogleSpeechEngine.transcribe()  — Google STT, retry on empty
        2. Auto-advance check  — gap > 3s + criteria → advance verse
        3. CorrectionEngine.process_utterance()
        4. IntentDetector.detect()  — REFERENCE / NAVIGATION / CROSS_REFERENCE / IGNORE
        5. Bible text matching  — text_buffer → BibleSearch.search_best()
           → If match + consensus → FreeShow + auto_advance + search_scope
        6. ReferenceBuilder.process(corrected_text)  — filler-tolerant state machine
        7. Builder scope → narrow BibleSearch if book+chapter known
        8. Confidence filter  — skip if < config.min_confidence
        9. IGNORE → skip
        10. NAVIGATION → SermonContext → FreeShow
        11. REFERENCE/CROSS_REFERENCE → if builder complete → FreeShow + auto_advance
        12. Catch-all exception handler → log + continue (no crash)
        13. Per-utterance timing breakdown logged (SR, Corr, Intent, Bible, Ctx, FS, Total)
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| STT empty/fail | Retry once, then skip silently |
| STT exception (RequestError) | Caught in engine, returns empty → skip |
| Processing pipeline exception | `except Exception` logs with exc_info, continues loop |
| FreeShow offline | `ConnectionError`/`Timeout` logged, no crash |
| FreeShow unknown book | `ValueError` caught, logged |
| PortAudioError | Logged, prompts mic re-selection |
| SIGTERM | Graceful shutdown via signal handler |
| Microphone disconnect | PortAudioError → choose another mic |

---

## Test Suite

| File | Tests | Scope |
|------|-------|-------|
| `test_parser.py` | 308 | Normalizer output, parser `BibleReference.canonical`, intent detection |
| `test_corpus.py` | 488 | Validates all `church_corpus.yaml` entries against parser + normalizer |
| `test_reference_builder.py` | 13 | ReferenceBuilder state machine (multi-utterance, filler tolerance, range, timeout, consume) |
| `test_e2e.py` | 13 | Full pipeline with mocks (STT, FreeShow, auto-advance, error recovery, navigation) |

All 809 tests: `python test_parser.py && python test_corpus.py && python test_reference_builder.py && python test_e2e.py`

---

## CLI Arguments

| Flag | Effect |
|------|--------|
| `--list-mics` | List available microphones and exit |
| `--mic N` | Skip interactive picker, use device N |
| `--mode {FAST,BALANCED,ACCURATE}` | Model hint (unused by Google STT) |
| `--model NAME` | Override model name (unused by Google STT) |
| `--language {AUTO,ENGLISH,TELUGU}` | Language hint for STT |
| `--dry-run` | Don't send to FreeShow |
