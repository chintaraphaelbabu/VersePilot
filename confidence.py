from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import NamedTuple

import books

logger = logging.getLogger("verses.confidence")


class ConfidenceResult(NamedTuple):
    overall: float
    book: float
    chapter: float
    verse: float
    builder: float
    context: float
    bible_search: float
    correction: float
    reasons: list[str]


def _book_score(alias: str, canonical: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    alias_lower = alias.lower()
    canonical_lower = canonical.lower()
    if alias_lower == canonical_lower:
        reasons.append("exact book alias")
        return 1.00, reasons
    for entry in books.BOOKS:
        if entry.canonical != canonical:
            continue
        for a in entry.aliases:
            if a.lower() == alias_lower:
                reasons.append("exact book alias")
                return 1.00, reasons
        for a in entry.telugu_aliases:
            if a.lower() == alias_lower:
                reasons.append("exact book alias")
                return 1.00, reasons
    if alias_lower in __import__("normalizer", fromlist=["ROMANIZED_LOOKUP"]).ROMANIZED_LOOKUP:
        reasons.append("romanized book alias")
        return 0.95, reasons
    try:
        from rapidfuzz import fuzz
        for entry in books.BOOKS:
            if entry.canonical != canonical:
                continue
            for a in entry.aliases:
                sim = fuzz.ratio(a.lower(), alias_lower) / 100.0
                if sim < 1.0:
                    reasons.append(f"fuzzy book alias (sim={sim:.2f})")
                    return sim, reasons
    except ImportError:
        pass
    reasons.append("unknown book match")
    return 0.85, reasons


def _num_score(value: int, raw: str | None) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if raw is not None and raw.isdigit():
        reasons.append(f"exact {raw}")
        return 1.00, reasons
    if raw is not None:
        from spoken_numbers import NUMBER_WORDS
        if raw.lower() in NUMBER_WORDS:
            reasons.append(f"spoken number ({raw})")
            return 0.95, reasons
    reasons.append("corrected number")
    return 0.90, reasons


def _builder_score(
    utterance_count: int,
    had_timeout: bool,
    is_complete: bool,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 1.00
    if utterance_count > 1:
        score += 0.05
        reasons.append(f"built across {utterance_count} utterances")
    if had_timeout:
        score -= 0.10
        reasons.append("timeout recovery")
    if not is_complete:
        score = min(score, 0.70)
        reasons.append("partial completion")
    score = max(0.0, min(score, 1.0))
    return score, reasons


def _context_score(
    prev_book: str | None, prev_chapter: int | None,
    cur_book: str, cur_chapter: int,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if prev_book == cur_book and prev_chapter == cur_chapter:
        reasons.append("same chapter continuation")
        return 1.05, reasons
    if prev_book == cur_book:
        reasons.append("same book continuation")
        return 1.03, reasons
    reasons.append("new reference")
    return 1.00, reasons


def _bible_score(fuzzy_score: float | None) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if fuzzy_score is None:
        reasons.append("no bible search")
        return 0.90, reasons
    s = fuzzy_score / 100.0
    reasons.append(f"bible match (score={s:.2f})")
    return s, reasons


def _correction_score(correction_count: int, versions: int) -> tuple[float, list[str]]:
    reasons: list[str] = []
    penalty = (correction_count + versions - 1) * 0.03
    score = max(0.70, 1.00 - penalty)
    if correction_count > 0:
        reasons.append(f"{correction_count} correction(s)")
    if versions > 1:
        reasons.append(f"{versions} version(s)")
    return score, reasons


def compute(
    *,
    book_alias: str,
    book_canonical: str,
    chapter_raw: str | None = None,
    chapter_value: int | None = None,
    verse_raw: str | None = None,
    verse_value: int | None = None,
    builder_utterance_count: int = 1,
    builder_had_timeout: bool = False,
    builder_is_complete: bool = True,
    prev_book: str | None = None,
    prev_chapter: int | None = None,
    bible_fuzzy_score: float | None = None,
    correction_count: int = 0,
    correction_versions: int = 1,
) -> ConfidenceResult:
    book_s, book_r = _book_score(book_alias, book_canonical)
    ch_s, ch_r = _num_score(chapter_value, chapter_raw) if chapter_value is not None else (1.00, [])
    ve_s, ve_r = _num_score(verse_value, verse_raw) if verse_value is not None else (1.00, [])
    bld_s, bld_r = _builder_score(builder_utterance_count, builder_had_timeout, builder_is_complete)
    ctx_s, ctx_r = _context_score(prev_book, prev_chapter, book_canonical, chapter_value or 1)
    bib_s, bib_r = _bible_score(bible_fuzzy_score)
    cor_s, cor_r = _correction_score(correction_count, correction_versions)

    overall = round(
        (book_s * 0.30 + ch_s * 0.15 + ve_s * 0.15 +
         bld_s * 0.10 + ctx_s * 0.10 + bib_s * 0.10 + cor_s * 0.10),
        2,
    )

    all_reasons = book_r + ch_r + ve_r + bld_r + ctx_r + bib_r + cor_r

    return ConfidenceResult(
        overall=overall,
        book=book_s,
        chapter=ch_s,
        verse=ve_s,
        builder=bld_s,
        context=ctx_s,
        bible_search=bib_s,
        correction=cor_s,
        reasons=all_reasons,
    )


def log(result: ConfidenceResult, label: str = "confidence") -> None:
    logger.info(
        "%s | overall=%.2f book=%.2f ch=%.2f ve=%.2f "
        "bld=%.2f ctx=%.2f bib=%.2f cor=%.2f | reasons: %s",
        label,
        result.overall, result.book, result.chapter, result.verse,
        result.builder, result.context, result.bible_search, result.correction,
        "; ".join(result.reasons),
    )
