from __future__ import annotations

import json
import os
from typing import NamedTuple

from rapidfuzz import fuzz


BOOK_ID_TO_CANONICAL: dict[int, str] = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
    15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
    20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
    28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
    33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
    38: "Zechariah", 39: "Malachi", 40: "Matthew", 41: "Mark", 42: "Luke",
    43: "John", 44: "Acts", 45: "Romans", 46: "1 Corinthians",
    47: "2 Corinthians", 48: "Galatians", 49: "Ephesians", 50: "Philippians",
    51: "Colossians", 52: "1 Thessalonians", 53: "2 Thessalonians",
    54: "1 Timothy", 55: "2 Timothy", 56: "Titus", 57: "Philemon",
    58: "Hebrews", 59: "James", 60: "1 Peter", 61: "2 Peter", 62: "1 John",
    63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation",
}


class VerseInfo(NamedTuple):
    book: str
    chapter: int
    verse: int
    text: str


class SearchResult(NamedTuple):
    book: str
    chapter: int
    verse: int
    text: str
    score: float


class BibleSearch:
    def __init__(self, bible_path: str | None = None) -> None:
        if bible_path is None:
            bible_path = os.path.join(os.path.dirname(__file__), "telugu_bible.json")
        self._verses: list[VerseInfo] = []
        self._by_book_chapter: dict[tuple[str, int], list[VerseInfo]] = {}
        self._by_chapter_verse: dict[tuple[str, int, int], VerseInfo] = {}
        self._word_index: dict[str, set[int]] = {}
        self._ngram_index: dict[str, set[int]] = {}
        self._load(bible_path)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = text.lower().split()
        result: list[str] = []
        for t in tokens:
            t = t.strip(".,!?;:()\"'«»-–—\xad¸")
            if t:
                result.append(t)
        return result

    def _load(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for idx, entry in enumerate(data["verses"]):
            canon = BOOK_ID_TO_CANONICAL[entry["book"]]
            vi = VerseInfo(
                book=canon,
                chapter=entry["chapter"],
                verse=entry["verse"],
                text=entry["text"],
            )
            self._verses.append(vi)
            key = (canon, entry["chapter"])
            if key not in self._by_book_chapter:
                self._by_book_chapter[key] = []
            self._by_book_chapter[key].append(vi)
            cv_key = (canon, entry["chapter"], entry["verse"])
            self._by_chapter_verse[cv_key] = vi
            for word in self._tokenize(entry["text"]):
                if word not in self._word_index:
                    self._word_index[word] = set()
                self._word_index[word].add(idx)
            text_lower = entry["text"].lower()
            for i in range(len(text_lower) - 2):
                ng = text_lower[i:i + 3]
                if ng[0].isspace() or ng[1].isspace() or ng[2].isspace():
                    continue
                if ng not in self._ngram_index:
                    self._ngram_index[ng] = set()
                self._ngram_index[ng].add(idx)

    def get_verse(self, book: str, chapter: int, verse: int) -> VerseInfo | None:
        return self._by_chapter_verse.get((book, chapter, verse))

    def get_chapter_verses(self, book: str, chapter: int) -> list[VerseInfo]:
        return self._by_book_chapter.get((book, chapter), [])

    def _get_candidates(self, query: str) -> list[VerseInfo] | None:
        union_set: set[int] = set()

        query_words = self._tokenize(query)
        if query_words:
            for w in query_words:
                s = self._word_index.get(w)
                if s:
                    union_set |= s

        query_lower = query.lower()
        for i in range(len(query_lower) - 2):
            ng = query_lower[i:i + 3]
            if ng[0].isspace() or ng[1].isspace() or ng[2].isspace():
                continue
            s = self._ngram_index.get(ng)
            if s:
                union_set |= s

        if not union_set:
            return None

        if len(union_set) >= len(self._verses) * 0.95:
            return None

        return [self._verses[i] for i in sorted(union_set)]

    def search(
        self,
        query: str,
        *,
        search_scope: tuple[str, int] | None = None,
        top_n: int = 3,
        min_score: float = 40.0,
    ) -> list[SearchResult]:
        if search_scope:
            book, chapter = search_scope
            candidates = self._by_book_chapter.get((book, chapter), [])
            if not candidates:
                candidates = self._verses
        else:
            indexed = self._get_candidates(query)
            candidates = indexed if indexed is not None else self._verses

        results: list[SearchResult] = []
        for vi in candidates:
            score = fuzz.partial_ratio(query, vi.text)
            if score >= min_score:
                results.append(SearchResult(
                    book=vi.book, chapter=vi.chapter,
                    verse=vi.verse, text=vi.text, score=score,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]

    def might_be_bible(self, text: str) -> bool:
        tokens = self._tokenize(text)
        for t in tokens:
            if t in self._word_index:
                return True
        return False

    def search_best(
        self,
        query: str,
        *,
        search_scope: tuple[str, int] | None = None,
        min_score: float = 40.0,
    ) -> SearchResult | None:
        results = self.search(query, search_scope=search_scope, top_n=1, min_score=min_score)
        return results[0] if results else None
