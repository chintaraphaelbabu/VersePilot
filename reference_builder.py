from __future__ import annotations

import logging
import re
import time
from enum import Enum, auto
from typing import Any

from normalizer import tokenize, classify, Token, normalize_spoken_numbers
from normalizer import _NUMBERED_BASE, _single_book_lookup
from parser import BibleReference


logger = logging.getLogger("verses.reference_builder")


class BuilderState(Enum):
    WAITING_BOOK = auto()
    WAITING_CHAPTER = auto()
    WAITING_VERSE = auto()
    WAITING_RANGE_END = auto()
    COMPLETE = auto()


RANGE_INDICATORS = {
    "\u0c28\u0c41\u0c02\u0c21\u0c3f",  # \u0ce8\u0cc1\u0c02\u0c21\u0c3f
    "\u0c28\u0c41\u0c02\u0c1a\u0c3f",  # \u0ce8\u0cc1\u0c02\u0c1a\u0c3f
    "\u0c35\u0c30\u0c15\u0c41",        # \u0ce7\u0cb0\u0c95\u0cc1
    "\u0c26\u0c3e\u0c15\u0c3e",
    "nundi", "nunchi", "varaku", "dakha", "daka",
    "through", "to",
    "-", "\u2013", "\u2014",
}


class ReferenceBuilder:
    """State machine that accumulates Bible reference info across utterances.

    States:
      WAITING_BOOK      — waiting for any book name
      WAITING_CHAPTER   — book known, waiting for chapter number
      WAITING_VERSE     — chapter known, waiting for verse number
      WAITING_RANGE_END — verse known, waiting for range end verse
      COMPLETE          — full reference (book+ch+verse) or (book+ch+verse+end)
    """

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self._reset()

    # ── public API ────────────────────────────────────────────

    def process(self, text: str) -> None:
        """Feed a new utterance into the builder."""
        if not text or not text.strip():
            self._log_state()
            return

        text = normalize_spoken_numbers(text)
        tokens = tokenize(text)
        classified = classify(tokens)

        self._utterance_had_ref = False
        self._process_classified(classified)
        # ponytail: Complete on filler utterance so split STT chunks
        # build the same ref as a single utterance would.
        if not self._utterance_had_ref:
            if self.state == BuilderState.WAITING_VERSE and self.verse is not None:
                self.state = BuilderState.COMPLETE
                self.last_reference_time = time.time()
            elif self.state == BuilderState.WAITING_RANGE_END:
                self.state = BuilderState.COMPLETE
                self.last_reference_time = time.time()
        self._log_state()

    def current_reference(self) -> BibleReference | None:
        if self.book is None:
            return None
        if self.chapter is None:
            return None
        if self.verse is None and self.state != BuilderState.WAITING_VERSE:
            return BibleReference(
                canonical=f"{self.book} {self.chapter}",
                book=self.book,
                chapter=self.chapter,
            )
        if self.verse is None:
            return BibleReference(
                canonical=f"{self.book} {self.chapter}",
                book=self.book,
                chapter=self.chapter,
            )
        if self.end_verse is not None:
            return BibleReference(
                canonical=f"{self.book} {self.chapter}:{self.verse}-{self.end_verse}",
                book=self.book,
                chapter=self.chapter,
                verse=self.verse,
                end_verse=self.end_verse,
            )
        return BibleReference(
            canonical=f"{self.book} {self.chapter}:{self.verse}",
            book=self.book,
            chapter=self.chapter,
            verse=self.verse,
        )

    def is_complete(self) -> bool:
        return self.state == BuilderState.COMPLETE

    def has_reference(self) -> bool:
        return self.book is not None

    def timeout(self) -> bool:
        if self.state == BuilderState.WAITING_BOOK:
            return False
        return (time.time() - self.last_reference_time) > self.timeout_seconds

    def check_timeout(self) -> bool:
        if self.timeout():
            logger.info("ReferenceBuilder timed out — resetting")
            self._reset()
            return True
        return False

    def consume(self) -> BibleReference | None:
        ref = self.current_reference()
        self._reset()
        return ref

    # ── internal state machine ────────────────────────────────

    def _reset(self) -> None:
        self.state = BuilderState.WAITING_BOOK
        self.book: str | None = None
        self.chapter: int | None = None
        self.verse: int | None = None
        self.end_verse: int | None = None
        self._pending_book_prefix: int | None = None
        self.last_reference_time: float = time.time()
        self.confidence: float = 0.0

    def _process_classified(self, classified: list[Token]) -> None:
        i = 0
        while i < len(classified):
            tok = classified[i]
            text_lower = tok.text.lower()

            # ── range indicator check (overrides type) ──
            if text_lower in RANGE_INDICATORS:
                self._utterance_had_ref = True
                if self.state == BuilderState.WAITING_VERSE and self.verse is not None:
                    self.state = BuilderState.WAITING_RANGE_END
                    self.last_reference_time = time.time()
                i += 1
                continue

            # ── new book causes reset ──
            if tok.type == "BOOK":
                self._utterance_had_ref = True
                self._handle_book(tok, i, classified)
                i += 1
                continue

            # ── state-specific handling ──
            if tok.type in ("NUMBER", "CHAPTER", "VERSE"):
                self._utterance_had_ref = True

            if self.state == BuilderState.WAITING_BOOK:
                self._on_waiting_book(tok)

            elif self.state == BuilderState.WAITING_CHAPTER:
                self._on_waiting_chapter(tok)

            elif self.state == BuilderState.WAITING_VERSE:
                remaining = classified[i + 1:]
                result = self._on_waiting_verse(tok, remaining)
                if result == "consumed":
                    pass
                elif result == "done":
                    return  # stop processing this utterance

            elif self.state == BuilderState.WAITING_RANGE_END:
                self._on_waiting_range_end(tok)

            elif self.state == BuilderState.COMPLETE:
                if tok.type == "NUMBER" and self.verse is not None:
                    # ponytail: extend range when new number arrives in COMPLETE state.
                    # Handles stutter/pause split: "13" "nunchi" "16" "nunchi" "33" → 13-33
                    if self.end_verse is None or tok.value > self.end_verse:
                        self.end_verse = tok.value
                        self.last_reference_time = time.time()
                        self.confidence = 0.99

            i += 1

    def _handle_book(self, tok: Token, i: int, classified: list[Token]) -> None:
        book_canon = tok.value
        if self._pending_book_prefix is not None:
            base = re.sub(r"^\d+\s+", "", book_canon).lower()
            nd = _NUMBERED_BASE.get(base)
            if nd and self._pending_book_prefix in nd:
                book_canon = nd[self._pending_book_prefix]

        if self.state != BuilderState.WAITING_BOOK:
            self._reset()

        self.book = book_canon
        self._pending_book_prefix = None
        self.last_reference_time = time.time()
        self.confidence = 0.6
        self.state = BuilderState.WAITING_CHAPTER

    def _on_waiting_book(self, tok: Token) -> None:
        if tok.type == "NUMBER":
            # Could be a numbered book prefix — store and wait for book name
            if self._pending_book_prefix is None:
                self._pending_book_prefix = tok.value

    def _on_waiting_chapter(self, tok: Token) -> None:
        if tok.type == "NUMBER" and self._pending_book_prefix is None:
            self.chapter = tok.value
            self.last_reference_time = time.time()
            self.confidence = 0.8
            self.state = BuilderState.WAITING_VERSE
        elif tok.type == "NUMBER" and self._pending_book_prefix is not None:
            # Previous book_prefix and now another number — resolve
            self._pending_book_prefix = None
            self.chapter = tok.value
            self.last_reference_time = time.time()
            self.confidence = 0.8
            self.state = BuilderState.WAITING_VERSE
        elif tok.type == "CHAPTER":
            pass  # ignore chapter marker, wait for number

    def _on_waiting_verse(self, tok: Token, remaining: list[Token]) -> str | None:
        if tok.type == "NUMBER":
            if self.verse is None:
                self.verse = tok.value
                self.last_reference_time = time.time()
                self.confidence = 0.93
                # Check if end_verse follows immediately in same utterance
                next_num = self._find_next_number(remaining, skip_range=False)
                if next_num is not None:
                    self.end_verse = next_num
                    self.last_reference_time = time.time()
                    self.confidence = 0.99
                    self.state = BuilderState.COMPLETE
                    return "consumed"
                # Check if range follows in same utterance
                if self._has_range_in(remaining):
                    self.state = BuilderState.WAITING_RANGE_END
                    return "consumed"
                # ponytail: No range/end in this utterance — don't complete.
                # Split chunks like "13" THEN "nundi" THEN "16" must build
                # the same reference as a single utterance.
                return "done"
        return None

    def _on_waiting_range_end(self, tok: Token) -> None:
        if tok.type == "NUMBER":
            self.end_verse = tok.value
            self.last_reference_time = time.time()
            self.confidence = 0.99
            self.state = BuilderState.COMPLETE

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    def _find_next_number(tokens: list[Token], skip_range: bool = True) -> int | None:
        for t in tokens:
            if skip_range and t.text.lower() in RANGE_INDICATORS:
                continue
            if t.type == "NUMBER":
                return t.value
            if t.type in ("CHAPTER", "VERSE"):
                continue
            if t.type in ("IGNORE", "UNKNOWN"):
                continue
            break
        return None

    @staticmethod
    def _has_range_in(tokens: list[Token]) -> bool:
        return any(t.text.lower() in RANGE_INDICATORS for t in tokens)

    def _log_state(self) -> None:
        logger.info(
            "ReferenceBuilder | State: %s | Book: %s | Chapter: %s | Verse: %s | Range: %s | Confidence: %.2f",
            self.state.name,
            self.book or "None",
            self.chapter or "None",
            self.verse or "None",
            self.end_verse or "None",
            self.confidence,
        )

    def __repr__(self) -> str:
        return (
            f"ReferenceBuilder(state={self.state.name}, "
            f"book={self.book!r}, ch={self.chapter}, v={self.verse}, "
            f"end={self.end_verse}, conf={self.confidence:.2f})"
        )
