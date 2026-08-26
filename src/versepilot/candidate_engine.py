"""Candidate Engine — maintains top N reference candidates with multi-factor scoring.

Replaces the single-reference pipeline: keeps candidates alive across utterances,
auto-decays stale ones, emits only when one is clearly dominant.

ponytail: no config file, no factory, no ABC. One class, two update methods,
one decide method, one log method.  Stdlib only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .parser import BibleReference

logger = logging.getLogger("verses.candidate_engine")

# ponytail: fixed weights, tuned once
_W = {
    "completeness": 0.25,
    "bible_search": 0.20,
    "context": 0.20,
    "confidence": 0.20,
    "recency": 0.15,
}

_EMIT_MARGIN = 0.15         # top must beat runner-up by this
_MIN_EMIT_SCORE = 0.60      # floor for emitting
_DECAY_PER_CYCLE = 0.08     # recency loss per utterance
_MAX_CANDIDATES = 5


@dataclass
class Candidate:
    """One possible reference with the five scoring factors."""
    reference: BibleReference
    completeness: float = 0.0       # 1.0 = full book+ch+verse+range
    bible_search_score: float = 0.0  # from BibleSearch (0-1)
    context_score: float = 0.0      # same scope as current?
    confidence: float = 0.0         # from builder.confidence
    recency: float = 1.0            # 1.0 fresh, decays each cycle
    cycles_since_update: int = 0
    evidence_count: int = 0

    @property
    def score(self) -> float:
        return (
            self.completeness * _W["completeness"]
            + self.bible_search_score * _W["bible_search"]
            + self.context_score * _W["context"]
            + self.confidence * _W["confidence"]
            + self.recency * _W["recency"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref": self.reference.canonical,
            "score": round(self.score, 3),
            "completeness": round(self.completeness, 3),
            "bible": round(self.bible_search_score, 3),
            "context": round(self.context_score, 3),
            "confidence": round(self.confidence, 3),
            "recency": round(self.recency, 3),
            "cycles_since_update": self.cycles_since_update,
            "evidence": self.evidence_count,
        }


class CandidateEngine:
    """Tracks up to _MAX_CANDIDATES references, scores them, decides when to emit."""

    def __init__(self) -> None:
        self._candidates: dict[str, Candidate] = {}
        self._cycle = 0
        self._last_emit: str | None = None
        self._log: list[str] = []

    # ── update sources ────────────────────────────────────────────

    def update_from_builder(self, builder: Any) -> None:
        """Feed builder state into engine after each utterance."""
        ref = builder.current_reference()
        if ref is None:
            return
        canonical = ref.canonical

        if canonical in self._candidates:
            c = self._candidates[canonical]
            c.evidence_count += 1
            c.cycles_since_update = 0
            c.recency = min(1.0, c.recency + 0.2)
        else:
            c = Candidate(reference=ref, evidence_count=1)
            self._candidates[canonical] = c

        # ponytail: completeness from builder state, not re-parsed
        if builder.verse is not None and builder.end_verse is not None:
            c.completeness = 1.00
        elif builder.verse is not None:
            c.completeness = 0.95
        elif builder.chapter is not None:
            c.completeness = 0.70
        else:
            c.completeness = 0.40

        c.confidence = max(c.confidence, builder.confidence or 0.0)

        # Context: same book+chapter as builder's current scope
        if builder.book and builder.chapter:
            c.context_score = (
                1.0 if (ref.book.lower() == builder.book.lower()
                        and ref.chapter == builder.chapter)
                else 0.5 if ref.book.lower() == builder.book.lower()
                else 0.0
            )

    def update_bible_score(self, bible_match: Any, search_scope: tuple | None) -> None:
        """Feed BibleSearch match into engine."""
        if bible_match is None:
            return
        canonical = f"{bible_match.book} {bible_match.chapter}:{bible_match.verse}"

        if canonical in self._candidates:
            c = self._candidates[canonical]
            c.bible_search_score = max(c.bible_search_score, bible_match.score / 100.0)
            c.cycles_since_update = 0
            c.recency = min(1.0, c.recency + 0.2)
            c.evidence_count += 1
        else:
            ref = BibleReference(
                canonical=canonical,
                book=bible_match.book,
                chapter=bible_match.chapter,
                verse=bible_match.verse,
            )
            c = Candidate(
                reference=ref,
                bible_search_score=bible_match.score / 100.0,
                completeness=0.95,
                confidence=0.90,
                evidence_count=1,
            )
            self._candidates[canonical] = c

        if search_scope:
            c.context_score = (
                1.0 if (bible_match.book.lower() == search_scope[0].lower()
                        and bible_match.chapter == search_scope[1])
                else 0.5 if bible_match.book.lower() == search_scope[0].lower()
                else 0.0
            )

    # ── lifecycle ─────────────────────────────────────────────────

    def _decay(self) -> None:
        for c in self._candidates.values():
            if c.cycles_since_update > 0:
                c.recency = max(0.0, c.recency - _DECAY_PER_CYCLE)
            c.cycles_since_update += 1

    def _prune(self) -> None:
        """Drop low-scoring old candidates; cap to _MAX_CANDIDATES."""
        to_remove = [
            k for k, c in self._candidates.items()
            if c.score < 0.20 and c.cycles_since_update > 3
        ]
        for k in to_remove:
            del self._candidates[k]
        if len(self._candidates) > _MAX_CANDIDATES:
            sorted_c = sorted(
                self._candidates.items(), key=lambda x: -x[1].score
            )
            for k, _ in sorted_c[_MAX_CANDIDATES:]:
                del self._candidates[k]

    def new_cycle(self) -> None:
        """Call after each utterance processed."""
        self._cycle += 1
        self._decay()
        self._prune()

    # ── decision ──────────────────────────────────────────────────

    def decide(self) -> BibleReference | None:
        """Return dominant candidate, or None if no clear winner."""
        if not self._candidates:
            return None
        ranked = sorted(self._candidates.values(), key=lambda c: -c.score)
        top = ranked[0]
        if top.score < _MIN_EMIT_SCORE:
            return None
        if len(ranked) > 1:
            margin = top.score - ranked[1].score
            if margin < _EMIT_MARGIN:
                return None
        if top.reference.canonical == self._last_emit:
            return None
        self._last_emit = top.reference.canonical
        return top.reference

    # ── observability ─────────────────────────────────────────────

    def snapshot(self) -> list[dict[str, Any]]:
        ranked = sorted(self._candidates.values(), key=lambda c: -c.score)
        return [c.to_dict() for c in ranked]

    def log(self) -> str:
        snapshot = self.snapshot()
        lines = [
            f"CandidateEngine cycle {self._cycle} — "
            f"{len(snapshot)} candidate(s)"
        ]
        for c in snapshot:
            lines.append(
                f"  {c['ref']:30s} "
                f"score={c['score']:.2f} "
                f"C={c['completeness']:.2f} "
                f"B={c['bible']:.2f} "
                f"X={c['context']:.2f} "
                f"F={c['confidence']:.2f} "
                f"R={c['recency']:.2f} "
                f"age={c['cycles_since_update']} "
                f"ev={c['evidence']}"
            )
        text = "\n".join(lines)
        self._log.append(text)
        return text

    def get_log(self) -> list[str]:
        return list(self._log)
