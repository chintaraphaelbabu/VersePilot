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
        from normalizer import normalize_telugu_bible_reference
        text = normalize_telugu_bible_reference(text)
        text = normalize_spoken_numbers(text)
        text = text.lower()
        text = text.replace("chapters", " ")
        text = text.replace("chapter", " ")
        text = text.replace("verses", " ")
        text = text.replace("verse", " ")
        text = text.replace("v.", " ")
        text = text.replace("ch.", " ")
        text = text.replace("అధ్యాయము", " ")
        text = text.replace("అధ్యాయం", " ")
        text = text.replace("వచనములు", " ")
        text = text.replace("వచనాలు", " ")
        text = text.replace("వచనము", " ")
        text = text.replace("వచనం", " ")
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
                    # Verify it's on word boundaries (or at least check boundary characters)
                    # to prevent matching parts of other words
                    # Since we normalized, we can check boundaries:
                    start_boundary = exact_index == 0 or text[exact_index - 1] == ' '
                    end_boundary = (exact_index + len(normalized_alias)) == len(text) or text[exact_index + len(normalized_alias)] == ' '
                    if start_boundary and end_boundary:
                        candidate = _BookMatch(entry, exact_index, exact_index + len(normalized_alias), 100)
                        if best is None or candidate.score > best.score:
                            best = candidate
                        continue

                # Fuzzy matching with window alignment
                alias_words = normalized_alias.split()
                text_words = text.split()
                if not alias_words or not text_words:
                    continue

                window = len(alias_words)
                for start_w in range(0, max(1, len(text_words) - window + 1)):
                    candidate_str = " ".join(text_words[start_w : start_w + window])
                    if fuzz is not None:
                        score = int(fuzz.ratio(normalized_alias, candidate_str))
                    else:
                        score = int(SequenceMatcher(None, normalized_alias, candidate_str).ratio() * 100)

                    if score >= self.fuzzy_threshold:
                        # Find indices in the normalized text
                        char_start = text.find(candidate_str)
                        if char_start == -1:
                            char_start = 0
                            for w in text_words[:start_w]:
                                char_start += len(w) + 1
                        char_end = char_start + len(candidate_str)
                        candidate_match = _BookMatch(entry, char_start, char_end, score)
                        if best is None or candidate_match.score > best.score:
                            best = candidate_match
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
            r"(?P<chapter>\d{1,3})\s+(?P<verse>\d{1,3})\s+(?P<end_verse>\d{1,3})",
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

            # Validate bounds as requested: chapter up to 150, verse up to 176
            if chapter > 150:
                return None
            if verse is not None and verse > 176:
                return None
            if end_verse is not None and end_verse > 176:
                return None

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