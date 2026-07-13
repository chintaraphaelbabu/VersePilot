from __future__ import annotations

import logging

from parser import BibleReference

logger = logging.getLogger("verses")


class AutoAdvance:
    def __init__(self, book: str, chapter: int, verse: int, end_verse: int = 999) -> None:
        self.book = book
        self.chapter = chapter
        self.current_verse = verse
        self.end_verse = end_verse
        self.speech_since_advance: float = 0.0
        self.segments_since_advance: int = 0
        self.ready: bool = False

    def process_advance(self, start_time: float, last_speech_end: float | None) -> BibleReference | None:
        if not self.ready or last_speech_end is None:
            return None

        gap = start_time - last_speech_end
        if gap > 10.0:
            self.segments_since_advance = 0
            self.speech_since_advance = 0.0
            return None

        if gap > 3.0 and (self.segments_since_advance >= 3 or self.speech_since_advance >= 4.0):
            if self.current_verse < self.end_verse:
                self.current_verse += 1
                self.speech_since_advance = 0.0
                self.segments_since_advance = 0
                return BibleReference(
                    canonical=f"{self.book} {self.chapter}:{self.current_verse}",
                    book=self.book,
                    chapter=self.chapter,
                    verse=self.current_verse,
                )

        return None

    def update_counters(self, segment_duration: float) -> None:
        self.speech_since_advance += segment_duration
        self.segments_since_advance += 1
        if not self.ready:
            self.ready = True
            self.speech_since_advance = 0.0
            self.segments_since_advance = 0

    @property
    def finished(self) -> bool:
        return self.current_verse >= self.end_verse
