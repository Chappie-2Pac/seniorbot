"""In-memory STM/MTM/LTM state and conservative lexical retrieval.

The public layer contains no user records and performs no implicit disk writes.
Applications can add an explicit persistence adapter around this state object.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional


MemoryLevel = Literal["stm", "mtm", "ltm"]

_STOPWORDS = {
    "and",
    "are",
    "das",
    "der",
    "die",
    "ein",
    "eine",
    "for",
    "have",
    "ich",
    "in",
    "ist",
    "the",
    "to",
    "und",
    "was",
    "with",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(value: Any) -> set[str]:
    text = str(value or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", text)
        if token not in _STOPWORDS
    }


@dataclass
class MemoryRecord:
    content: Any
    level: MemoryLevel = "stm"
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "explicit"
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now)
    updated_at: Optional[str] = None

    def touch(self) -> None:
        self.updated_at = _now()


class MemoryState:
    """A bounded memory coordinator with explicit promotion and deletion."""

    def __init__(self, *, max_entries: int = 128) -> None:
        self.max_entries = max(0, int(max_entries))
        self._records: dict[str, MemoryRecord] = {}

    def remember(
        self,
        content: Any,
        *,
        level: MemoryLevel = "stm",
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        source: str = "explicit",
    ) -> MemoryRecord:
        record = MemoryRecord(
            content=content,
            level=level,
            importance=max(0.0, min(1.0, float(importance))),
            tags=list(tags or []),
            metadata=dict(metadata or {}),
            source=source,
        )
        self._records[record.record_id] = record
        self._trim()
        return record

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self._records.get(record_id)

    def promote(self, record_id: str, level: MemoryLevel) -> bool:
        record = self.get(record_id)
        if record is None:
            return False
        record.level = level
        record.touch()
        return True

    def forget(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None

    def clear(self) -> int:
        count = len(self._records)
        self._records.clear()
        return count

    def recent(self, limit: int = 5) -> list[MemoryRecord]:
        if limit <= 0:
            return []
        return sorted(self._records.values(), key=lambda item: item.created_at)[-limit:]

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        scored: list[tuple[float, MemoryRecord]] = []
        for record in self._records.values():
            if record.metadata.get("hidden"):
                continue
            overlap = query_tokens & _tokens(record.content)
            if not overlap:
                continue
            score = len(overlap) / len(query_tokens)
            scored.append((score, record))
        scored.sort(key=lambda item: (-item[0], -item[1].importance, item[1].created_at))
        return [
            {
                "record_id": record.record_id,
                "level": record.level,
                "score": round(score, 3),
                "snippet": str(record.content)[:240],
                "metadata": dict(record.metadata),
            }
            for score, record in scored[: max(0, limit)]
        ]

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "record_id": record.record_id,
                "level": record.level,
                "importance": record.importance,
                "tags": list(record.tags),
                "source": record.source,
                "created_at": record.created_at,
            }
            for record in self.recent(limit=len(self._records))
        ]

    def _trim(self) -> None:
        if self.max_entries <= 0:
            return
        while len(self._records) > self.max_entries:
            candidate = min(
                self._records.values(),
                key=lambda item: (item.importance, item.created_at),
            )
            self._records.pop(candidate.record_id, None)
