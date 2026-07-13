from __future__ import annotations

import logging
import time

logging.basicConfig(level=logging.WARNING)

from reference_builder import ReferenceBuilder, BuilderState


def test_single_utterance():
    b = ReferenceBuilder(timeout_seconds=20)
    b.process("John 3 16")
    ref = b.current_reference()
    assert b.is_complete(), f"Expected complete, got {b.state}"
    assert ref is not None
    assert ref.canonical == "John 3:16", f"Got {ref.canonical}"
    print("  PASS: single utterance")


def test_multi_utterance_progressive():
    b = ReferenceBuilder()
    # Utterance 1: book name with filler
    b.process("\u0c2e\u0c28\u0c2e\u0c02\u0c26\u0c30\u0c02 \u0c06\u0c26\u0c3f\u0c15\u0c3e\u0c02\u0c21\u0c2e\u0c41")
    assert b.state == BuilderState.WAITING_CHAPTER
    assert b.book == "Genesis"
    assert not b.is_complete()

    # Utterance 2: pure filler — should NOT reset
    b.process("\u0c24\u0c46\u0c30\u0c3f\u0c1a\u0c3f\u0c28\u0c1f\u0c4d\u0c32\u0c2f\u0c3f\u0c24\u0c47")
    assert b.state == BuilderState.WAITING_CHAPTER
    assert b.book == "Genesis", "Filler should not clear book!"

    # Utterance 3: chapter
    b.process("18\u0c35 \u0c05\u0c27\u0c4d\u0c2f\u0c3e\u0c2f\u0c2e\u0c41")
    assert b.state == BuilderState.WAITING_VERSE
    assert b.chapter == 18

    # Utterance 4: verse + range
    b.process("13 \u0c28\u0c41\u0c02\u0c1a\u0c3f")
    assert b.state == BuilderState.WAITING_RANGE_END
    assert b.verse == 13

    # Utterance 5: end verse
    b.process("33 \u0c35\u0c30\u0c15\u0c41")
    assert b.is_complete()
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Genesis 18:13-33", f"Got {ref.canonical}"
    print("  PASS: multi-utterance progressive")


def test_filler_tolerance():
    b = ReferenceBuilder()
    b.process("Genesis")
    assert b.state == BuilderState.WAITING_CHAPTER
    assert b.book == "Genesis"

    # Multiple filler utterances
    for filler in ["\u0c2e\u0c28\u0c2e\u0c41 \u0c07\u0c2a\u0c4d\u0c2a\u0c41\u0c21\u0c41 \u0c1a\u0c42\u0c26\u0c4d\u0c26\u0c3e\u0c02",
                   "\u0c06 \u0c24\u0c46\u0c30\u0c3f\u0c1a\u0c3f\u0c28\u0c1f\u0c4d\u0c32\u0c2f\u0c3f\u0c24\u0c47",
                   "\u0c2a\u0c4d\u0c30\u0c3f\u0c2f\u0c41\u0c32\u0c3e\u0c30\u0c3e",
                   "\u0c38\u0c30\u0c47",
                   "\u0c05\u0c2f\u0c3f\u0c24\u0c47"]:
        b.process(filler)
        assert b.state == BuilderState.WAITING_CHAPTER, f"Filler {filler!r} reset state!"
        assert b.book == "Genesis"

    b.process("1 1")
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Genesis 1:1", f"Got {ref.canonical}"
    print("  PASS: filler tolerance")


def test_range_same_utterance():
    b = ReferenceBuilder()
    b.process("\u0c06\u0c26\u0c3f\u0c15\u0c3e\u0c02\u0c21\u0c2e\u0c41 18 13 \u0c28\u0c41\u0c02\u0c1a\u0c3f 33")
    ref = b.current_reference()
    assert b.is_complete()
    assert ref is not None
    assert ref.canonical == "Genesis 18:13-33", f"Got {ref.canonical}"
    print("  PASS: range same utterance")


def test_end_verse_same_utterance():
    b = ReferenceBuilder()
    b.process("Psalms 23 1 5")
    ref = b.current_reference()
    assert b.is_complete()
    assert ref is not None
    assert ref.canonical == "Psalms 23:1-5", f"Got {ref.canonical}"
    print("  PASS: end verse same utterance")


def test_new_book_overrides():
    b = ReferenceBuilder()
    b.process("John 3")
    assert b.chapter == 3
    assert b.state == BuilderState.WAITING_VERSE

    # New book resets
    b.process("Psalms 23 1")
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Psalms 23:1", f"Got {ref.canonical}"
    print("  PASS: new book override")


def test_ignore_non_reference():
    b = ReferenceBuilder()
    b.process("\u0c2e\u0c28 \u0c2a\u0c4d\u0c30\u0c3e\u0c30\u0c4d\u0c25\u0c28")
    assert b.state == BuilderState.WAITING_BOOK
    assert b.book is None
    print("  PASS: ignore non-reference")


def test_timeout():
    b = ReferenceBuilder(timeout_seconds=1)
    b.process("Genesis 1")
    assert b.chapter == 1

    # Override last_reference_time to simulate timeout
    b.last_reference_time = time.time() - 5
    assert b.timeout()
    assert b.check_timeout()  # This resets
    assert b.state == BuilderState.WAITING_BOOK
    assert b.book is None
    print("  PASS: timeout")


def test_consume():
    b = ReferenceBuilder()
    b.process("Romans 8 28")
    ref = b.consume()
    assert ref is not None
    assert ref.canonical == "Romans 8:28"
    assert b.state == BuilderState.WAITING_BOOK
    assert b.book is None
    print("  PASS: consume")


def test_verse_only_no_range():
    b = ReferenceBuilder()
    b.process("Matthew 5 3")
    assert b.is_complete()
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Matthew 5:3"
    print("  PASS: verse only no range")


def test_chapter_only():
    b = ReferenceBuilder()
    b.process("Psalms 23")
    assert b.state == BuilderState.WAITING_VERSE
    assert b.chapter == 23
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Psalms 23"
    print("  PASS: chapter only")


def test_numbered_book():
    b = ReferenceBuilder()
    b.process("1 Timothy 3 16")
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "1 Timothy 3:16", f"Got {ref.canonical}"
    print("  PASS: numbered book")


def test_reference_after_filler():
    b = ReferenceBuilder()
    b.process("\u0c06\u0c2e\u0c47\u0c28\u0c4d")  # non-bible
    assert b.state == BuilderState.WAITING_BOOK
    b.process("\u0c06\u0c26\u0c3f\u0c15\u0c3e\u0c02\u0c21\u0c2e\u0c41 1 1")
    ref = b.current_reference()
    assert ref is not None
    assert ref.canonical == "Genesis 1:1"
    print("  PASS: reference after filler")


if __name__ == "__main__":
    tests = [
        test_single_utterance,
        test_multi_utterance_progressive,
        test_filler_tolerance,
        test_range_same_utterance,
        test_end_verse_same_utterance,
        test_new_book_overrides,
        test_ignore_non_reference,
        test_timeout,
        test_consume,
        test_verse_only_no_range,
        test_chapter_only,
        test_numbered_book,
        test_reference_after_filler,
    ]
    for t in tests:
        t()
    print(f"\nALL {len(tests)} TESTS PASSED")
