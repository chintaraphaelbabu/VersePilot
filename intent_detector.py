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

# Custom word boundary pattern that handles both ASCII and Telugu unicode characters (including combining marks)
_L_BOUND = r"(?<![a-zA-Z0-9\u0C00-\u0C7F])"
_R_BOUND = r"(?![a-zA-Z0-9\u0C00-\u0C7F])"

# Precompile list of book aliases (including canonical names)
_raw_aliases: list[str] = []
for book in BOOKS:
    _raw_aliases.append(book.canonical.lower())
    for alias in book.aliases:
        _raw_aliases.append(alias.lower())

# Deduplicate and sort aliases by length descending to match longer multi-word aliases first
_raw_aliases = list(set(_raw_aliases))
_raw_aliases.sort(key=len, reverse=True)

_aliases = [re.escape(a) for a in _raw_aliases]

# Regex to match any book name/alias with custom boundaries
_BOOK_PATTERN = r"(?:" + "|".join(_aliases) + r")"
_BOOK_REGEX = re.compile(_L_BOUND + _BOOK_PATTERN + _R_BOUND, re.IGNORECASE)

# Dynamically construct number words or digits pattern
_all_num_words = (
    list(ENGLISH_NUMBER_WORDS.keys()) +
    list(TELUGU_ONESE.keys()) +
    list(TELUGU_TEENS.keys()) +
    list(TELUGU_TENS.keys()) +
    list(TELUGU_HUNDREDS.keys())
)
_all_num_words.sort(key=len, reverse=True)
_NUMBER_PATTERN = r"(?:\d+|" + "|".join(re.escape(w) for w in _all_num_words) + r")"
_NUMBER_REGEX = re.compile(_L_BOUND + _NUMBER_PATTERN + _R_BOUND, re.IGNORECASE)

# Reference pattern: book alias followed by optional dividers and digits/number words
_REFERENCE_REGEX = re.compile(
    _L_BOUND + _BOOK_PATTERN + r"\s*(?:chapter|chapters|verse|verses|ch|v|[:.\s])+\s*" + _NUMBER_PATTERN,
    re.IGNORECASE
)

# Navigation patterns using custom boundaries
_NAVIGATION_REGEXES = [
    re.compile(_L_BOUND + r"next\s+verse" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:previous|prev)\s+verse" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"next\s+chapter" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:previous|prev)\s+chapter" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"go\s+back" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"return\s+to\s+(?:the\s+)?passage" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"go\s+back\s+to\s+passage" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"continue(?:\s+reading)?" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"verse\s+\d+" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"chapter\s+\d+" + _R_BOUND, re.IGNORECASE),
    # Telugu & Mixed commands
    re.compile(_L_BOUND + r"తరువాతి\s+వచనం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"next\s+వచనం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:previous|prev|ముందటి)\s+వచనం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"తరువాతి\s+అధ్యాయం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"next\s+అధ్యాయం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:previous|prev|ముందటి)\s+అధ్యాయం" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:verse|వచనం)\s+\d+" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:chapter|అధ్యాయం)\s+\d+" + _R_BOUND, re.IGNORECASE),
    re.compile(_L_BOUND + r"(?:continue|తిరగండి|వెళ్దాం|చూద్దాం|గమనించండి)" + _R_BOUND, re.IGNORECASE),
]

# Cross-reference keywords
_CROSS_REF_KEYWORDS = [
    "see also",
    "compare with",
    "compare",
    "look at",
    "cross reference",
    "cross-reference",
    "చూడండి",
    "పోల్చి"
]


class IntentDetector:
    def __init__(self) -> None:
        pass

    def detect(self, text: str) -> tuple[str, float]:
        # Normalize spoken numbers (e.g. "one" -> "1") and clean text
        normalized = normalize_spoken_numbers(text)
        cleaned = normalized.strip().lower()

        # 1. Check if a Bible book is present
        has_book = False
        exact_ref_match = False

        book_match = _BOOK_REGEX.search(cleaned)
        if book_match:
            has_book = True
            if _REFERENCE_REGEX.search(cleaned) or _REFERENCE_REGEX.search(text.lower()):
                exact_ref_match = True
        elif fuzz is not None:
            # Fuzzy match books
            best_score = 0
            for alias in _raw_aliases:
                if len(alias) < 4:
                    if re.search(_L_BOUND + re.escape(alias) + _R_BOUND, cleaned):
                        has_book = True
                        break
                    continue
                score = fuzz.partial_ratio(alias, cleaned)
                if score >= 85:
                    if score > best_score:
                        best_score = score
                        has_book = True

        if has_book:
            # Check if it is a Cross Reference
            is_cross_ref = False
            for kw in _CROSS_REF_KEYWORDS:
                if kw in cleaned:
                    is_cross_ref = True
                    break

            has_number = bool(re.search(r"\b\d+\b", cleaned) or _NUMBER_REGEX.search(cleaned) or _NUMBER_REGEX.search(text.lower()))

            if is_cross_ref:
                if exact_ref_match or has_number:
                    return "CROSS_REFERENCE", 0.95
                return "CROSS_REFERENCE", 0.60  # Low confidence if no verse/chapter numbers

            # Check if it is a Reference
            if exact_ref_match or has_number:
                return "REFERENCE", 0.90

            # Mentions a book but doesn't have reference structure (e.g., "The Bible says Romans...")
            return "IGNORE", 1.0

        # 2. Navigation Check (only if no Bible book is present)
        for regex in _NAVIGATION_REGEXES:
            if regex.search(cleaned) or regex.search(text.lower()):
                return "NAVIGATION", 1.0

        # Default to IGNORE
        return "IGNORE", 1.0
