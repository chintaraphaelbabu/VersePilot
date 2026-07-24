"""Scan replay timeline JSONs for unknown words that consistently map to a book.

Only considers entries where the builder JUST completed (builder_completed=True),
so we know the raw utterance caused a specific book to be detected.  Then finds
words in that raw transcript that aren't already known aliases."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

from normalizer import _single_book_lookup, ROMANIZED_LOOKUP, IGNORE_WORDS
from books import BOOKS

REPLAY_DIR = "replay"

_WORD_RE = re.compile(r"[a-zA-Z\u0C00-\u0C7F]{3,}")

# ponytail: only filter really common junk; most noise is eliminated by
# the builder_completed gate so we don't need a huge stop-list.
_COMMON = {
    "the", "and", "for", "from", "this", "that", "with", "was", "are",
    "but", "you", "all", "can", "has", "its", "not", "our", "out",
    "see", "she", "two", "who", "will", "what", "have",
    "please", "book", "chapter", "verse", "verses", "chapters",
    "scripture", "let", "just", "god", "lord", "like", "going",
    "next", "previous", "back", "read",
    # Telugu common words unlikely to be book aliases
    "అందుకు", "అని", "అన్ని", "అన్నీ", "అయిన", "అయినా", "అయితే",
    "అర్థం", "అలా", "ఆయన", "ఆయనను", "ఆయనే", "ఆలాగే",
    "ఇందుకు", "ఇక్కడ", "ఇప్పుడు", "ఇలా", "ఈయన",
    "ఉండడం", "ఉండి", "ఉండు", "ఉన్న", "ఉన్నా", "ఉన్నాను",
    "ఉన్నాము", "ఉన్నారు", "ఉన్నావు", "ఉన్నాడు",
    "ఎంత", "ఎందుకు", "ఎందుకంటే", "ఎక్కడ", "ఎప్పుడు",
    "ఎప్పుడైతే", "ఎవరు", "ఎవరైతే", "ఎవరైనా",
    "ఏమి", "ఏమిటి", "ఏమైనా",
    "ఒక", "ఒకటి", "ఒకడు", "ఒకరు",
    "కనుక", "కాక", "కాకపోతే", "కాకుండా", "కాబట్టి",
    "కావాలి", "కూడా", "కొంత", "కొన్ని", "కోసం",
    "గనుక", "గురించి",
    "చాలా", "చేసి", "చేస్తూ",
    "తన", "తనకు", "తనను", "తర్వాత", "తరువాత",
    "తెలుసు", "తో", "తోడు",
    "దాని", "దానికి", "దానిని", "దాన్ని", "దినము",
    "దీని", "దీనికి", "దీనిని", "దేనికి",
    "నా", "నాకు", "నాతో", "నిన్ను", "నీకు",
    "నుంచి", "నుండి", "నేను", "నేడు",
    "పత్రిక", "ప్రకారం", "ప్రతి",
    "బడిన", "బదులు",
    "మంచి", "మన", "మనకు", "మనము", "మనం", "మనిషి",
    "మనిషిని", "మధ్య", "మరి", "మరియు", "మరొక",
    "మా", "మాకు", "మాట", "మాట్లాడు",
    "ముందు", "మూడవ", "మూడవదిగా", "మొదటి", "మొదటిగా",
    "మొట్టమొదటిగా",
    "యెహోవా", "యేసు",
    "రాకడ", "రెండవ", "రెండవది",
    "లేదు", "లేని", "లేనప్పుడు",
    "లో", "లోకంలో", "లోకాన్ని",
    "వంటి", "వచ్చి", "వచ్చిన", "వచ్చినది", "వచ్చినప్పుడు",
    "వచ్చు", "వచ్చే", "వట్టి", "వద్దు",
    "వరకు", "వలన", "వలె", "వాక్యము", "వాక్యం",
    "వాక్యాన్ని", "వాటిని", "వాడు", "వారి", "వారికి",
    "వారిగా", "వారు", "విల్",
    "విషయం", "విషయము", "వీటిని", "వీరు",
    "వెళ్ళి", "వేరు", "వైపు",
    "శాశ్వత", "శుభ", "శ్రీ",
    "సంగతి", "సమయం", "సరే", "సహాయం", "స్థలము",
}

_KNOWN_ALIASES: set[str] = set()
for entry in BOOKS:
    for a in entry.aliases:
        _KNOWN_ALIASES.add(a.lower())
_KNOWN_ALIASES.update(ROMANIZED_LOOKUP.keys())
_KNOWN_ALIASES.update(IGNORE_WORDS)


def word_is_known(w: str) -> bool:
    wl = w.lower()
    if _single_book_lookup(wl) is not None:
        return True
    if wl in _KNOWN_ALIASES:
        return True
    if wl in _COMMON:
        return True
    return False


def main():
    cand: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    total_entries = 0
    completed_entries = 0

    for d in sorted(os.listdir(REPLAY_DIR)):
        jp = os.path.join(REPLAY_DIR, d, "timeline.json")
        if not os.path.isfile(jp):
            continue
        timeline = json.load(open(jp, "r", encoding="utf-8"))
        for entry in timeline:
            total_entries += 1
            raw = (entry.get("raw_transcript") or "").strip()
            book = entry.get("builder_book")
            if not raw or not book:
                continue
            # Only consider entries where the builder JUST completed on this
            # utterance — guarantees the raw text triggered the book match.
            if not entry.get("builder_completed"):
                continue
            completed_entries += 1
            for m in _WORD_RE.finditer(raw):
                w = m.group().lower()
                if not word_is_known(w):
                    cand[w][book] += 1

    # Filter: >= 3 total, always same book, confidence > 0.95
    suggestions: list[dict] = []
    for word, books in sorted(cand.items()):
        total_obs = sum(books.values())
        if total_obs < 3:
            continue
        if len(books) != 1:
            continue
        canon = next(iter(books))
        count = books[canon]
        confidence = round(count / total_obs, 2) if total_obs else 0
        if confidence <= 0.95:
            continue
        suggestions.append({
            "word": word,
            "book": canon,
            "count": count,
            "confidence": confidence,
        })

    lines = [
        "# alias_suggestions.yaml",
        "# Auto-generated from replay timeline analysis.",
        "# Review and manually add high-confidence suggestions to books.py or normalizer.py.",
        f"# Scanned {total_entries} timeline entries; {completed_entries} had builder_completed=True.",
        "",
        "suggestions:",
    ]
    for s in suggestions:
        lines.append(f'  {s["word"]}:')
        lines.append(f'    book: "{s["book"]}"')
        lines.append(f"    count: {s['count']}")
        lines.append(f"    confidence: {s['confidence']}")
        lines.append("")

    out = os.path.join(REPLAY_DIR, "alias_suggestions.yaml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(suggestions)} suggestions to {out}")
    for s in suggestions:
        print(f"  {s['word']} -> {s['book']} (count={s['count']}, conf={s['confidence']})")


if __name__ == "__main__":
    main()
