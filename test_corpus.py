from __future__ import annotations

import yaml
from pathlib import Path
from parser import BibleReferenceParser

parser = BibleReferenceParser()


def load_corpus(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_corpus() -> int:
    corpus = load_corpus(Path(__file__).parent / "church_corpus.yaml")
    failed = 0
    total = 0

    for i, entry in enumerate(corpus):
        inp = entry["input"]
        total += 1
        ref = parser.parse(inp)

        has_book = "book" in entry and entry["book"] is not None
        has_chapter = "chapter" in entry and entry["chapter"] is not None
        has_verse = "verse" in entry and entry["verse"] is not None
        has_end_verse = "end_verse" in entry and entry["end_verse"] is not None

        exp_book = entry.get("book")
        exp_chapter = entry.get("chapter")
        exp_verse = entry.get("verse")
        exp_end_verse = entry.get("end_verse")

        if not has_book:
            if ref is not None:
                print(f"FAIL [{total}]: {inp!r} -> {ref.canonical!r} (expected None)")
                failed += 1
            continue

        if ref is None:
            print(f"FAIL [{total}]: {inp!r} -> None (expected {exp_book} {exp_chapter}:{exp_verse})")
            failed += 1
            continue

        errors: list[str] = []
        if ref.book != exp_book:
            errors.append(f"book={ref.book!r} != {exp_book!r}")
        if has_chapter and ref.chapter != exp_chapter:
            errors.append(f"chapter={ref.chapter} != {exp_chapter}")
        if has_verse and ref.verse != exp_verse:
            errors.append(f"verse={ref.verse} != {exp_verse}")
        if has_end_verse and ref.end_verse != exp_end_verse:
            errors.append(f"end_verse={ref.end_verse} != {exp_end_verse}")
        if not has_verse and ref.verse is not None and has_chapter:
            errors.append(f"verse={ref.verse} != None (expected chapter-only)")
        if not has_chapter and ref.chapter is not None:
            errors.append(f"chapter={ref.chapter} != None (expected book-only)")
        if not has_end_verse and ref.end_verse is not None:
            errors.append(f"end_verse={ref.end_verse} != None")

        if errors:
            print(f"FAIL [{total}]: {inp!r} -> {'; '.join(errors)}")
            failed += 1

    if failed:
        print(f"\nCorpus: {total - failed}/{total} passed, {failed} FAILED")
    else:
        print(f"Corpus: {total}/{total} passed")
    return failed


if __name__ == "__main__":
    raise SystemExit(test_corpus())
