from __future__ import annotations

import re
from books import BOOKS
from spoken_numbers import (
    normalize_spoken_numbers,
    ENGLISH_NUMBER_WORDS,
    TELUGU_ONESE,
    TELUGU_TEENS,
    TELUGU_TENS,
    TELUGU_HUNDREDS
)

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

REPAIR_MARKERS = {"sorry", "no", "actually", "correction", "కాదు", "లేదు", "అంటే", "ఆ"}


class MutableBibleReference:
    def __init__(self) -> None:
        self.book: str | None = None
        self.chapter: int | None = None
        self.verse: int | None = None
        self.end_verse: int | None = None
        self.last_assigned: str | None = None  # 'book', 'chapter', 'verse', 'end_verse'


class CorrectionEngine:
    def __init__(self) -> None:
        self.ref = MutableBibleReference()
        self.should_repair = False

    def reset(self) -> None:
        self.ref = MutableBibleReference()
        self.should_repair = False

    def tokenize(self, text: str) -> list[str]:
        # We want to find book aliases (from longest to shortest) and replace them with temporary tokens
        aliases_with_canonical = []
        for entry in BOOKS:
            aliases_with_canonical.append((entry.canonical, entry.canonical))
            for alias in entry.aliases:
                aliases_with_canonical.append((alias, entry.canonical))

        # Sort by length descending to match longer strings first
        aliases_with_canonical.sort(key=lambda x: len(x[0]), reverse=True)

        normalized = normalize_spoken_numbers(text)
        lowered = normalized.lower()

        _L_BOUND = r"(?<![a-zA-Z0-9\u0C00-\u0C7F])"
        _R_BOUND = r"(?![a-zA-Z0-9\u0C00-\u0C7F])"

        replaced = lowered
        book_replacements = {}
        for alias, canonical in aliases_with_canonical:
            pattern = _L_BOUND + re.escape(alias.lower()) + _R_BOUND
            matches = list(re.finditer(pattern, replaced))
            if matches:
                for match in reversed(matches):
                    placeholder = f"__BOOK_{len(book_replacements)}__"
                    book_replacements[placeholder] = canonical
                    replaced = replaced[:match.start()] + placeholder + replaced[match.end():]

        raw_tokens = replaced.strip().split()

        tokens = []
        for t in raw_tokens:
            if t in book_replacements:
                tokens.append(f"BOOK:{book_replacements[t]}")
            else:
                tokens.append(t)
        return tokens

    def process_utterance(self, text: str) -> str:
        self.reset()
        tokens = self.tokenize(text)

        for token in tokens:
            token_lower = token.lower()

            if token_lower in REPAIR_MARKERS:
                self.should_repair = True
                continue

            # Check if it's a book
            if token.startswith("BOOK:"):
                matched_book = token.split(":", 1)[1]
                self.ref.book = matched_book
                self.ref.chapter = None
                self.ref.verse = None
                self.ref.last_assigned = 'book'
                self.should_repair = False
                continue

            # Check if it's a number
            if token.isdigit():
                num = int(token)
                if self.should_repair:
                    if self.ref.last_assigned == 'chapter':
                        self.ref.chapter = num
                    elif self.ref.last_assigned == 'verse':
                        self.ref.verse = num
                    elif self.ref.last_assigned == 'book':
                        self.ref.chapter = num
                        self.ref.last_assigned = 'chapter'
                    self.should_repair = False
                else:
                    if self.ref.chapter is None:
                        self.ref.chapter = num
                        self.ref.last_assigned = 'chapter'
                    elif self.ref.verse is None:
                        self.ref.verse = num
                        self.ref.last_assigned = 'verse'
                    else:
                        self.ref.end_verse = num
                        self.ref.last_assigned = 'end_verse'
                continue

            # If it's another word, check fuzzy book match
            if fuzz is not None:
                best_score = 0
                best_book = None
                for entry in BOOKS:
                    for alias in entry.aliases:
                        # Skip very short aliases to prevent false positives
                        if len(alias) < 4:
                            continue
                        score = fuzz.ratio(alias.lower(), token_lower)
                        if score >= 85 and score > best_score:
                            best_score = score
                            best_book = entry.canonical
                if best_book:
                    self.ref.book = best_book
                    self.ref.chapter = None
                    self.ref.verse = None
                    self.ref.last_assigned = 'book'
                    self.should_repair = False
                    continue

        # Reconstruct the corrected final utterance
        if self.ref.book:
            parts = [self.ref.book]
            if self.ref.chapter is not None:
                parts.append(str(self.ref.chapter))
                if self.ref.verse is not None:
                    parts.append(str(self.ref.verse))
                if self.ref.end_verse is not None:
                    parts.append(str(self.ref.end_verse))
            return " ".join(parts)

        return text
