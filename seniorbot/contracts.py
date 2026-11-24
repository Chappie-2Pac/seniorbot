"""Stable data contracts shared by ASR, LLM, TTS, and orchestration layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AdapterStatus:
    """A readiness result that does not expose adapter internals."""

    name: str
    ready: bool
    detail: str = ""


class AdapterBase:
    """Small lifecycle default for test doubles and local adapters."""

    def start(self) -> AdapterStatus:
        return AdapterStatus(self.__class__.__name__, True, "ready")

    def stop(self) -> None:
        return None


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.2
    system_prompt: Optional[str] = None
    route_hint: Optional[str] = None


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens: int = 0
    latency_seconds: float = 0.0
    first_token_seconds: Optional[float] = None


@dataclass(frozen=True)
class LLMStreamChunk:
    text: str
    is_final: bool = False
    tokens: int = 0


@dataclass(frozen=True)
class STTResult:
    text: str
    confidence: float = 0.0
    latency_seconds: float = 0.0
    capture_latency_seconds: float = 0.0
    ack_latency_seconds: float = 0.0


@dataclass(frozen=True)
class TTSResult:
    audio_path: str = ""
    latency_seconds: float = 0.0
