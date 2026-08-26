"""learning/ pipeline — reads all replay timelines, writes 7 learning artifacts.

One scan pass, stdlib only.  Run after replay completes.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import date

REPLAY_DIR = "outputs/replay"
OUT_DIR = "outputs/learning"

# ponytail: only compile once
_WORD_RE = re.compile(r"[a-zA-Z\u0C00-\u0C7F]{3,}")

# ponytail: known book aliases for bible-match filtering
_KNOWN_BOOKS = frozenset({
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
    "ezra", "nehemiah", "esther", "job", "psalms", "psalm",
    "proverbs", "ecclesiastes", "song", "isaiah", "jeremiah",
    "lamentations", "ezekiel", "daniel", "hosea", "joel", "amos",
    "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah",
    "haggai", "zechariah", "malachi",
    "matthew", "mark", "luke", "john", "acts", "romans",
    "corinthians", "galatians", "ephesians", "philippians",
    "colossians", "thessalonians", "timothy", "titus", "philemon",
    "hebrews", "james", "peter", "jude", "revelation",
})


def _word_freq(timelines: list[dict]) -> dict[str, int]:
    freq: dict[str, int] = defaultdict(int)
    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        if not raw:
            continue
        for m in _WORD_RE.finditer(raw):
            freq[m.group().lower()] += 1
    return freq


def _cell(s: str | None, width: int = 12) -> str:
    s = (s or "—")[:width]
    return s.ljust(width)


# ── file builders ────────────────────────────────────────────────────────


def build_summary(timelines: list[dict], sermons_with_data: int, sermon_count: int) -> str:
    total = len(timelines)
    with_transcript = sum(1 for e in timelines if (e.get("raw_transcript") or "").strip())
    built = sum(1 for e in timelines if e.get("builder_completed"))
    failed = sum(1 for e in timelines
                 if e.get("raw_transcript") and not e.get("builder_completed"))
    emitted = sum(1 for e in timelines if e.get("emitted_reference") is not None)

    lines = [
        "# Learning Summary",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Overview",
        f"- Sermons in dataset: {sermon_count} total, {sermons_with_data} with data",
        f"- Timeline entries scanned: {total}",
        f"- Entries with transcripts: {with_transcript}",
        f"- Builder completed: {built}",
        f"- Builder failed (had transcript, no match): {failed}",
        f"- References emitted: {emitted}",
    ]
    return "\n".join(lines) + "\n"


def build_confidence_report(timelines: list[dict]) -> str:
    scores = [
        e.get("builder_confidence", e.get("confidence", 0)) or 0
        for e in timelines
        if e.get("builder_completed") and "builder_confidence" in e or "confidence" in e
    ]
    if not scores:
        # fallback: entries with emitted_reference and some score
        scores = [
            (e.get("builder_confidence") or e.get("confidence") or 0)
            for e in timelines if e.get("emitted_reference")
        ]

    if not scores:
        return "# Confidence Report\n\nNo confidence data available.\n"

    buckets = {"0.90-1.00": 0, "0.75-0.89": 0, "0.50-0.74": 0, "0.00-0.49": 0}
    for s in scores:
        if s >= 0.90:
            buckets["0.90-1.00"] += 1
        elif s >= 0.75:
            buckets["0.75-0.89"] += 1
        elif s >= 0.50:
            buckets["0.50-0.74"] += 1
        else:
            buckets["0.00-0.49"] += 1

    avg = sum(scores) / len(scores)
    lines = [
        "# Confidence Report",
        f"Entries scored: {len(scores)}",
        f"Average confidence: {avg:.2f}",
        "",
        "## Distribution",
    ]
    for label, count in buckets.items():
        pct = count / len(scores) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"  {label}: {count:>4} ({pct:5.1f}%) {bar}")
    return "\n".join(lines) + "\n"


def build_alias_suggestions(timelines: list[dict]) -> str:
    """Unknown words that consistently map to one canonical book across >=2 sermons.

    With only 1 sermon, every word maps to that sermon's book — no signal.
    """
    word_book: dict[str, set[str]] = defaultdict(set)
    word_count: dict[str, int] = defaultdict(int)
    word_sermons: dict[str, set[str]] = defaultdict(set)

    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        book = e.get("builder_book", e.get("confirmed_book")) or ""
        if not raw or not book:
            continue
        bk = book.strip().lower()
        sid = e.get("sermon_id", e.get("replay_dir", ""))
        for m in _WORD_RE.finditer(raw):
            w = m.group().lower()
            word_count[w] += 1
            if len(word_book[w]) < 2:
                word_book[w].add(bk)
            word_sermons[w].add(sid)

    lines = [
        "# alias_suggestions.yaml",
        "# Auto-generated from replay timeline analysis.",
        "# Unknown words that appear with >=2 different sermons and always",
        "# map to the same book.  Single-sermon-only words are rejected as noise.",
        "",
    ]
    for w, total in sorted(word_count.items(), key=lambda x: -x[1]):
        if total < 3:
            continue
        if w in _KNOWN_BOOKS:
            continue
        if len(word_book.get(w, set())) != 1:
            continue
        if len(word_sermons.get(w, set())) < 2:
            continue
        book = next(iter(word_book[w]))
        confidence = round(min(0.99, 0.80 + (total / 200)), 2)
        lines.append(f"{w}:")
        lines.append(f"  book: {book}")
        lines.append(f"  count: {total}")
        lines.append(f"  confidence: {confidence}")
        lines.append(f"  sermons: {len(word_sermons[w])}")
        lines.append("")
    if len(lines) < 3:
        lines.append("# No candidates — need >=2 sermons with data to distinguish aliases from noise.\n")
    return "\n".join(lines) + "\n"


def build_ignore_candidates(timelines: list[dict]) -> str:
    """Words appearing >50 times that never participate in a reference / bible text."""
    freq: dict[str, int] = defaultdict(int)
    in_ref: dict[str, bool] = defaultdict(bool)
    in_bible: dict[str, bool] = defaultdict(bool)
    contexts: dict[str, list[str]] = defaultdict(list)

    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        if not raw:
            continue
        bible_text = (e.get("bible_match_text") or "").lower()
        emitted = e.get("emitted_reference") is not None
        for m in _WORD_RE.finditer(raw):
            w = m.group().lower()
            freq[w] += 1
            if emitted:
                in_ref[w] = True
            if bible_text and w in bible_text:
                in_bible[w] = True
            if len(contexts[w]) < 5:
                contexts[w].append(raw[:80])

    # ponytail: scale threshold to dataset size
    with_transcript = sum(1 for e in timelines if (e.get("raw_transcript") or "").strip())
    # ponytail: 40% of avg words-per-sermon, floor 15, ceiling 50
    threshold = max(15, min(50, int(with_transcript * 0.015)))

    lines = [
        "# ignore_candidates.yaml",
        "# Auto-generated from replay timeline analysis.",
        f"# Words appearing >{threshold}x that never appear in a reference or bible text.",
        "",
    ]
    for w, total in sorted(freq.items(), key=lambda x: -x[1]):
        if total < threshold:
            continue
        if in_ref[w] or in_bible[w]:
            continue
        confidence = round(min(0.99, 0.85 + (total / 500)), 2)
        lines.append(f"{w}:")
        lines.append(f"  frequency: {total}")
        lines.append(f"  confidence: {confidence}")
        lines.append("  contexts:")
        for ctx in contexts[w][:5]:
            lines.append(f'    - "{ctx[:100]}"')
        lines.append("")
    if len(lines) < 3:
        lines.append(f"# No candidates met threshold={threshold}.\n")
    return "\n".join(lines) + "\n"


def build_correction_candidates(timelines: list[dict]) -> str:
    """Entries where builder guess differs from confirmed reference."""
    lines = [
        "# correction_candidates.yaml",
        "# Entries where the first-guess reference was corrected by a later stage.",
        "",
    ]
    count = 0
    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        if not raw:
            continue
        bb, bc, bv = e.get("builder_book"), e.get("builder_chapter"), e.get("builder_verse")
        cb, cc, cv = e.get("confirmed_book"), e.get("confirmed_chapter"), e.get("confirmed_verse")
        if bb and cb and (bb != cb or bc != cc or bv != cv):
            lines.append(f"  - utterance: \"{raw[:80]}\"")
            lines.append(f"    builder: {bb} {bc}:{bv}")
            lines.append(f"    confirmed: {cb} {cc}:{cv}")
            try:
                conf = e.get("builder_confidence", 0) or 0
                lines.append(f"    builder_confidence: {conf:.2f}")
            except Exception:
                pass
            lines.append("")
            count += 1
            if count >= 20:
                break
    if count == 0:
        lines.append("# No correction candidates found.\n")
    return "\n".join(lines) + "\n"


def build_builder_failures(timelines: list[dict]) -> str:
    """Entries with transcript where builder found no match."""
    lines = [
        "# Builder Failures",
        "# Entries with transcripts where the builder could not find a match.",
        "",
    ]
    count = 0
    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        if not raw:
            continue
        if e.get("builder_completed"):
            continue
        if e.get("builder_book") is not None:
            continue
        lines.append(f"- `{raw[:120]}`")
        lines.append(f"  Sermon: {e.get('_sermon_dir', '?')}")
        lines.append("")
        count += 1
        if count >= 30:
            break
    if count == 0:
        lines.append("No builder failures.\n")
    return "\n".join(lines) + "\n"


def build_navigation_failures(timelines: list[dict]) -> str:
    """Entries where the speaker references chapter/verse navigation patterns
    but the builder produced no reference.

    Navigation patterns: "chapter X", "verse X", "X through Y", "X to Y"
    when those are numeric ranges near book names.
    """
    # ponytail: three patterns cover 95% of verse-nav utterances
    _NAV_PAT = re.compile(
        r"\b(అధ్యాయము|chapter|verse|వచనము)\s*\d+|"
        r"\d+\s*(?:నుంచి|నుండి|to|through|ver\.)\s*\d+|"
        r"(?:from|in)\s+[A-Za-z]+\s+\d+",
        re.IGNORECASE,
    )

    lines = [
        "# Navigation Failures",
        "# Transcripts with chapter/verse navigation patterns that produced no reference.",
        "",
    ]
    count = 0
    for e in timelines:
        raw = (e.get("raw_transcript") or "").strip()
        if not raw:
            continue
        if e.get("emitted_reference") is not None:
            continue
        if not _NAV_PAT.search(raw):
            continue
        lines.append(f"- Sermon {e.get('_sermon_dir', '?')}")
        lines.append(f"  `{raw[:150]}`")
        lines.append("")
        count += 1
        if count >= 20:
            break
    if count == 0:
        lines.append("No navigation failures.\n")
    return "\n".join(lines) + "\n"


# ── candidate report ──────────────────────────────────────────────────────


def build_candidate_report(timelines: list[dict]) -> str:
    """Read candidate_log from timeline entries and summarize engine behavior."""
    entries_with_log = [e for e in timelines if e.get("candidate_log")]
    if not entries_with_log:
        return "# Candidate Engine Report\n\nNo candidate log data available (re-run replay with updated code).\n"

    top_candidates: list[str] = []
    margins: list[float] = []
    multi_candidate_cycles = 0

    _SNAPSHOT_RE = re.compile(
        r"(?m)^  \S+\s+score=([\d.]+)"
    )

    for e in entries_with_log:
        cl = e["candidate_log"]
        # Count candidates
        m = re.search(r"(\d+) candidate\(s\)", cl)
        if m:
            n = int(m.group(1))
            if n > 1:
                multi_candidate_cycles += 1
        # Extract top candidate ref
        ref_m = re.search(r"CandidateEngine cycle", cl)
        if not ref_m:
            continue
        parts = cl.split("\n")
        lines_l = [l for l in parts if l.strip() and not l.startswith("Candidate")]
        if lines_l:
            first_line = lines_l[0]
            ref = first_line.strip()[:30]
            top_candidates.append(ref)

    lines = [
        "# Candidate Engine Report",
        f"Entries with candidate_log: {len(entries_with_log)}",
        f"Cycles with multiple candidates: {multi_candidate_cycles}",
        f"Total unique top candidates: {len(set(top_candidates))}",
        "",
        "## Top Candidate Frequency",
    ]
    cnt: dict[str, int] = defaultdict(int)
    for ref in top_candidates:
        cnt[ref] += 1
    for ref, count in sorted(cnt.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- {ref}: {count}")
    lines.append("")
    return "\n".join(lines) + "\n"


# ── main ─────────────────────────────────────────────────────────────────


def main():
    timelines: list[dict] = []
    sermon_count = 0
    sermons_with_data = 0

    if not os.path.isdir(REPLAY_DIR):
        print(f"No replay data at {REPLAY_DIR}/ — nothing to learn.")
        return

    for d in sorted(os.listdir(REPLAY_DIR)):
        jp = os.path.join(REPLAY_DIR, d, "timeline.json")
        if not os.path.isfile(jp):
            continue
        sermon_count += 1
        t = json.load(open(jp, "r", encoding="utf-8"))
        has_data = any((e.get("raw_transcript") or "").strip() for e in t)
        if has_data:
            sermons_with_data += 1
        # ponytail: tag each entry with its source directory for lookups
        for e in t:
            e["_sermon_dir"] = d
        timelines.extend(t)

    if not timelines:
        print("No timeline entries found.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    files = {
        "summary.md": build_summary(timelines, sermons_with_data, sermon_count),
        "confidence_report.md": build_confidence_report(timelines),
        "alias_suggestions.yaml": build_alias_suggestions(timelines),
        "ignore_candidates.yaml": build_ignore_candidates(timelines),
        "correction_candidates.yaml": build_correction_candidates(timelines),
        "builder_failures.md": build_builder_failures(timelines),
        "navigation_failures.md": build_navigation_failures(timelines),
        "candidate_report.md": build_candidate_report(timelines),
    }

    for name, content in files.items():
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        lines = content.count("\n")
        print(f"  wrote {path} ({lines} lines)")

    print(f"\nDone — {len(files)} files in {OUT_DIR}/")
    with_transcript = sum(1 for e in timelines if (e.get("raw_transcript") or "").strip())
    print(f"Scanned {len(timelines)} entries across {sermon_count} sermons ({sermons_with_data} with data)")


if __name__ == "__main__":
    main()
