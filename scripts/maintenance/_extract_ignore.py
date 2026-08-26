"""Scan replay timelines for high-frequency words that never participate in refs.

Threshold is auto-scaled to dataset size: 50% of the mean entries-per-sermon
with transcripts, so it adapts whether you have 100 or 10000 entries."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

REPLAY_DIR = "outputs/replay"

_WORD_RE = re.compile(r"[a-zA-Z\u0C00-\u0C7F]{3,}")


def main():
    freq: dict[str, int] = defaultdict(int)
    in_ref: dict[str, bool] = defaultdict(bool)
    in_bible: dict[str, bool] = defaultdict(bool)
    contexts: dict[str, list[str]] = defaultdict(list)
    total_entries = 0
    sermons_with_data = 0

    for d in sorted(os.listdir(REPLAY_DIR)):
        jp = os.path.join(REPLAY_DIR, d, "timeline.json")
        if not os.path.isfile(jp):
            continue
        timeline = json.load(open(jp, "r", encoding="utf-8"))
        sermon_has_data = False
        for entry in timeline:
            total_entries += 1
            raw = (entry.get("raw_transcript") or "").strip()
            if not raw:
                continue
            sermon_has_data = True

            bible_text = (entry.get("bible_match_text") or "").lower()
            emitted = entry.get("emitted_reference") is not None

            words_in_this = set()
            for m in _WORD_RE.finditer(raw):
                w = m.group().lower()
                words_in_this.add(w)
                freq[w] += 1
                if emitted:
                    in_ref[w] = True
                if bible_text and w in bible_text:
                    in_bible[w] = True

            # ponytail: store one context snippet per sermon per word
            for w in words_in_this:
                key = (w, d)
                if len(contexts[key]) < 3:
                    m = _WORD_RE.search(raw)
                    if m:
                        start = max(0, m.start() - 20)
                        end = min(len(raw), m.end() + 40)
                        ctx = raw[start:end].replace("\n", " ")
                    else:
                        ctx = raw[:80]
                    contexts[key].append(ctx)
        if sermon_has_data:
            sermons_with_data += 1

    # ponytail: adapt threshold to available data — min 50 but scale down
    # when the dataset is small so the output isn't always empty.
    avg_per_sermon = total_entries / max(sermons_with_data, 1)
    min_freq = max(10, min(50, int(avg_per_sermon * 0.4)))

    candidates = []
    for w, total in sorted(freq.items(), key=lambda x: -x[1]):
        if total < min_freq:
            continue
        if in_ref[w]:
            continue
        if in_bible[w]:
            continue
        ctxs = []
        for (word, sermon), snippet in sorted(contexts.items()):
            if word == w:
                ctxs.extend(snippet)
        confidence = round(min(0.99, 0.85 + (total / 500)), 2)
        candidates.append({
            "word": w,
            "frequency": total,
            "contexts": ctxs[:5],
            "confidence": confidence,
        })

    lines = [
        "# ignore_candidates.yaml",
        "# Auto-generated from replay timeline analysis.",
        "# Words appearing >N times that NEVER appeared in a reference emission",
        "# and NEVER appeared in Bible match text.",
        f"# Threshold auto-scaled to {min_freq} based on {total_entries} entries across {sermons_with_data} sermon(s) with data.",
        "# Review before adding to normalizer.py IGNORE_WORDS.",
        "",
    ]
    for c in candidates:
        lines.append(f'{c["word"]}:')
        lines.append(f'  frequency: {c["frequency"]}')
        lines.append(f'  confidence: {c["confidence"]}')
        lines.append("  contexts:")
        for ctx in c["contexts"]:
            lines.append(f'    - "{ctx[:100]}"')
        lines.append("")

    if not candidates:
        lines.append("# No candidates met the threshold.")

    out = os.path.join(REPLAY_DIR, "ignore_candidates.yaml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(candidates)} candidates to {out} (threshold={min_freq})")
    for c in candidates:
        print(f"  {c['word']}: freq={c['frequency']} conf={c['confidence']}")


if __name__ == "__main__":
    main()
