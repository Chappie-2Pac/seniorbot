"""Confidence-gated streaming decisions for incremental ASR text."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingConfig:
    enabled: bool = False
    early_response_min_chars: int = 36
    early_response_confidence: float = 0.7
    min_stable_updates: int = 2


@dataclass(frozen=True)
class StreamingChunk:
    text: str
    confidence: float = 0.0
    is_final: bool = False


@dataclass(frozen=True)
class StreamingDecision:
    text: str = ""
    confidence: float = 0.0
    is_final: bool = False
    should_respond: bool = False
    reason: str = ""


class StreamingController:
    def __init__(self, config: StreamingConfig) -> None:
        self.config = config
        self._last_text = ""
        self._stable_updates = 0

    def update(self, chunk: StreamingChunk) -> StreamingDecision:
        text = (chunk.text or "").strip()
        decision = StreamingDecision(text, chunk.confidence, chunk.is_final)
        if not text:
            return StreamingDecision(text=text, confidence=chunk.confidence, is_final=chunk.is_final, reason="empty")
        if text == self._last_text:
            self._stable_updates += 1
        else:
            self._last_text = text
            self._stable_updates = 1
        if chunk.is_final:
            return StreamingDecision(text, chunk.confidence, True, True, "final")
        if not self.config.enabled:
            return StreamingDecision(text, chunk.confidence, False, False, "streaming_disabled")
        if (
            len(text) >= self.config.early_response_min_chars
            and chunk.confidence >= self.config.early_response_confidence
            and self._stable_updates >= self.config.min_stable_updates
        ):
            return StreamingDecision(text, chunk.confidence, False, True, "early_stable")
        return StreamingDecision(text, chunk.confidence, False, False, "continue")
