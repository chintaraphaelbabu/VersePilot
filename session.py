from __future__ import annotations

import dataclasses

from auto_advance import AutoAdvance


SCOPE_RESET_TIMEOUT = 60.0


@dataclasses.dataclass
class SermonSession:
    last_reference: str | None = None
    auto_advance: AutoAdvance | None = None
    last_speech_end: float | None = None
    text_buffer: str = ""
    search_scope: tuple[str, int] | None = None
    last_search_time: float = 0.0
    match_history: list[tuple[str, int, float]] = dataclasses.field(default_factory=list)
