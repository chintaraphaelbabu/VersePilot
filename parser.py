from __future__ import annotations

import re
from difflib import SequenceMatcher
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover - optional dependency fallback
    fuzz = None

from books import BOOKS, BookEntry
from spoken_numbers import normalize_spoken_numbers


@dataclass(frozen=True)
class BibleReference:
    canonical: str
    book: str
    chapter: int
    verse: int | None = None
    end_verse: int | None = None


@dataclass(frozen=True)
class _BookMatch:
    entry: BookEntry
    start: int
    end: int
    score: int


class BibleReferenceParser:
    def __init__(self, fuzzy_threshold: int = 85) -> None:
        self.fuzzy_threshold = fuzzy_threshold
        self._book_entries = BOOKS

    def parse(self, text: str) -> BibleReference | None:
        normalized = self._normalize(text)
        match = self._find_book_match(normalized)
        if match is None:
            return None

        reference = self._extract_reference(match.entry.canonical, normalized[match.end :])
        if reference is None:
            return None

        return reference

    def _normalize(self, text: str) -> str:
        text = normalize_spoken_numbers(text)
        text = text.lower()
        text = text.replace("chapter", " ")
        text = text.replace("chapters", " ")
        text = text.replace("verse", " ")
        text = text.replace("verses", " ")
        text = text.replace("v.", " ")
        text = text.replace("ch.", " ")
        text = re.sub(r"[\.,;()\[\]{}]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _find_book_match(self, text: str) -> _BookMatch | None:
        best: _BookMatch | None = None
        for entry in self._book_entries:
            for alias in entry.aliases:
                normalized_alias = alias.lower()
                exact_index = text.find(normalized_alias)
                if exact_index != -1:
                    candidate = _BookMatch(entry, exact_index, exact_index + len(normalized_alias), 100)
                    if best is None or candidate.score > best.score:
                        best = candidate
                    continue

                score = self._fuzzy_score(normalized_alias, text)
                if score < self.fuzzy_threshold:
                    continue

                candidate = _BookMatch(entry, 0, len(normalized_alias), score)
                if best is None or candidate.score > best.score:
                    best = candidate
        return best

    def _fuzzy_score(self, alias: str, text: str) -> int:
        if fuzz is not None:
            return int(fuzz.partial_ratio(alias, text))

        if not alias or not text:
            return 0

        alias_words = alias.split()
        text_words = text.split()
        if not alias_words or not text_words:
            return 0

        best = 0.0
        window = len(alias_words)
        for start in range(0, max(1, len(text_words) - window + 1)):
            candidate = " ".join(text_words[start : start + window])
            score = SequenceMatcher(None, alias, candidate).ratio()
            if score > best:
                best = score
        return int(best * 100)

    def _extract_reference(self, book: str, tail: str) -> BibleReference | None:
        tail = tail.strip()
        if not tail:
            return None

        patterns = [
            r"(?P<chapter>\d{1,3})\s*[:.]\s*(?P<verse>\d{1,3})(?:\s*[-–]\s*(?P<end_verse>\d{1,3}))?",
            r"(?P<chapter>\d{1,3})\s+(?P<verse>\d{1,3})(?:\s*[-–]\s*(?P<end_verse>\d{1,3}))?",
            r"(?P<chapter>\d{1,3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, tail)
            if match is None:
                continue

            chapter = int(match.group("chapter"))
            verse_text = match.groupdict().get("verse")
            end_verse_text = match.groupdict().get("end_verse")

            verse = int(verse_text) if verse_text else None
            end_verse = int(end_verse_text) if end_verse_text else None

            canonical = book if verse is None else f"{book} {chapter}:{verse}"
            if end_verse is not None:
                canonical = f"{canonical}-{end_verse}"

            return BibleReference(
                canonical=canonical,
                book=book,
                chapter=chapter,
                verse=verse,
                end_verse=end_verse,
            )

        return None