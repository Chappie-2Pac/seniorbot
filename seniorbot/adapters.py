"""Adapter protocols keep hardware and model implementations outside the core."""

from __future__ import annotations

from typing import Iterable, Protocol

from .contracts import (
    AdapterStatus,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    STTResult,
    TTSResult,
)


class ASRAdapter(Protocol):
    def start(self) -> AdapterStatus: ...

    def transcribe(self, audio_path: str) -> STTResult: ...


class LLMAdapter(Protocol):
    def start(self) -> AdapterStatus: ...

    def generate(self, request: LLMRequest) -> LLMResponse: ...

    def stream_chunks(self, request: LLMRequest) -> Iterable[LLMStreamChunk]: ...


class TTSAdapter(Protocol):
    def start(self) -> AdapterStatus: ...

    def synthesize(self, text: str) -> TTSResult: ...
