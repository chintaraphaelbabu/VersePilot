from __future__ import annotations

import re
import time
from parser import BibleReference


def clean_text(text: str) -> str:
    from spoken_numbers import normalize_spoken_numbers
    text = normalize_spoken_numbers(text)
    text = text.lower()
    text = re.sub(r"[^\w\s\u0C00-\u0C7F]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_voice_command(text: str) -> str | tuple[str, int] | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None

    if "next verse" in cleaned or "తరువాతి వచనం" in cleaned or "next వచనం" in cleaned:
        return "next_verse"
    if "previous verse" in cleaned or "prev verse" in cleaned or "ముందటి వచనం" in cleaned or "previous వచనం" in cleaned or "prev వచనం" in cleaned:
        return "previous_verse"
    if "next chapter" in cleaned or "తరువాతి అధ్యాయం" in cleaned or "next అధ్యాయం" in cleaned:
        return "next_chapter"
    if "previous chapter" in cleaned or "prev chapter" in cleaned or "ముందటి అధ్యాయం" in cleaned or "previous అధ్యాయం" in cleaned or "prev అధ్యాయం" in cleaned:
        return "previous_chapter"
    if "go back" in cleaned or "వెనుకకు" in cleaned or "వెనక్కి" in cleaned:
        return "go_back"
    if "return to passage" in cleaned or "return to the passage" in cleaned or "go back to passage" in cleaned or "తిరిగి వెళ్దాం" in cleaned:
        return "return_to_passage"
    if "continue reading" in cleaned or cleaned == "continue" or "చూద్దాం" in cleaned or "వెళ్దాం" in cleaned:
        return "continue"

    # verse patterns: "verse 18" or "వచనం 18" or "వచనము 18"
    verse_match = re.search(r"(?:verse|వచనం|వచనము)\s+(\d+)", cleaned)
    if verse_match:
        return ("jump_to_verse", int(verse_match.group(1)))

    # Telugu ordinal-first pattern: "18 వ వచనం" (18th verse)
    verse_ord = re.search(r"(\d+)\s*వ\s*వచనం", cleaned)
    if verse_ord:
        return ("jump_to_verse", int(verse_ord.group(1)))

    # chapter patterns: "chapter 18" or "అధ్యాయం 18" or "అధ్యాయము 18"
    chapter_match = re.search(r"(?:chapter|అధ్యాయం|అధ్యాయము)\s+(\d+)", cleaned)
    if chapter_match:
        return ("jump_to_chapter", int(chapter_match.group(1)))

    # Telugu ordinal-first pattern: "18 వ అధ్యాయం" or "18 వ అధ్యాయము"
    ch_ord = re.search(r"(\d+)\s*వ\s*అధ్యాయం", cleaned)
    if ch_ord:
        return ("jump_to_chapter", int(ch_ord.group(1)))

    return None


def create_reference(book: str, chapter: int, verse: int | None = None, end_verse: int | None = None) -> BibleReference:
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


class SermonContext:
    def __init__(self) -> None:
        self.primary_reference: BibleReference | None = None
        self.displayed_reference: BibleReference | None = None
        self.history: list[BibleReference] = []
        self.last_command_time: float | None = None

    def _update_display(self, new_ref: BibleReference, push_history: bool = True) -> None:
        if push_history and self.displayed_reference is not None and self.displayed_reference != new_ref:
            self.history.append(self.displayed_reference)
        self.displayed_reference = new_ref

    def set_primary(self, reference: BibleReference) -> None:
        self._update_display(reference, push_history=True)
        self.primary_reference = reference

    def show_cross_reference(self, reference: BibleReference) -> None:
        self._update_display(reference, push_history=True)

    def next_verse(self) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        current_verse = self.primary_reference.style_verse if hasattr(self.primary_reference, "style_verse") else self.primary_reference.verse
        if current_verse is None:
            current_verse = 1
        new_verse = current_verse + 1
        new_ref = create_reference(self.primary_reference.book, self.primary_reference.chapter, new_verse)
        self.set_primary(new_ref)
        return new_ref

    def previous_verse(self) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        current_verse = self.primary_reference.verse
        if current_verse is None:
            current_verse = 1
        new_verse = max(1, current_verse - 1)
        new_ref = create_reference(self.primary_reference.book, self.primary_reference.chapter, new_verse)
        self.set_primary(new_ref)
        return new_ref

    def next_chapter(self) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        new_chapter = self.primary_reference.chapter + 1
        new_ref = create_reference(self.primary_reference.book, new_chapter, None)
        self.set_primary(new_ref)
        return new_ref

    def previous_chapter(self) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        new_chapter = max(1, self.primary_reference.chapter - 1)
        new_ref = create_reference(self.primary_reference.book, new_chapter, None)
        self.set_primary(new_ref)
        return new_ref

    def jump_to_verse(self, verse_num: int) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        new_ref = create_reference(self.primary_reference.book, self.primary_reference.chapter, verse_num)
        self.set_primary(new_ref)
        return new_ref

    def jump_to_chapter(self, chapter_num: int) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        new_ref = create_reference(self.primary_reference.book, chapter_num, None)
        self.set_primary(new_ref)
        return new_ref

    def return_to_primary(self) -> BibleReference | None:
        if self.primary_reference is None:
            return None
        self._update_display(self.primary_reference, push_history=True)
        return self.primary_reference

    def go_back(self) -> BibleReference | None:
        if not self.history:
            return self.displayed_reference
        new_ref = self.history.pop()
        self._update_display(new_ref, push_history=False)
        return new_ref

    def process_input(self, text: str, reference: BibleReference | None) -> BibleReference | None:
        self.last_command_time = time.time()
        if reference is not None:
            if self.primary_reference is None:
                self.set_primary(reference)
            else:
                self.show_cross_reference(reference)
            return self.displayed_reference

        # Process voice commands
        command = parse_voice_command(text)
        if command is None:
            return None

        if isinstance(command, tuple):
            cmd_name, val = command
            if cmd_name == "jump_to_verse":
                return self.jump_to_verse(val)
            elif cmd_name == "jump_to_chapter":
                return self.jump_to_chapter(val)
        else:
            if command == "next_verse" or command == "continue":
                return self.next_verse()
            elif command == "previous_verse":
                return self.previous_verse()
            elif command == "next_chapter":
                return self.next_chapter()
            elif command == "previous_chapter":
                return self.previous_chapter()
            elif command == "return_to_passage":
                return self.return_to_primary()
            elif command == "go_back":
                return self.go_back()

        return None
