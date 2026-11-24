"""Deterministic fast/full LLM routing with bounded, memory-only caching."""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Optional

from .adapters import LLMAdapter
from .contracts import AdapterStatus, LLMRequest, LLMResponse, LLMStreamChunk


@dataclass
class RoutePolicy:
    fast_max_chars: int = 240
    full_keywords: list[str] = field(default_factory=list)
    fast_keywords: list[str] = field(default_factory=list)

    def select_route(self, prompt: str) -> str:
        text = (prompt or "").strip().casefold()
        if any(word.casefold() in text for word in self.full_keywords):
            return "full"
        if any(word.casefold() in text for word in self.fast_keywords):
            return "fast"
        return "fast" if len(text) <= self.fast_max_chars else "full"


@dataclass(frozen=True)
class CacheEntry:
    text: str
    tokens: int
    expires_at: float


class ResponseCache:
    def __init__(
        self,
        *,
        max_entries: int = 128,
        ttl_seconds: float = 300.0,
        normalizer: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.max_entries = max(0, int(max_entries))
        self.ttl_seconds = float(ttl_seconds)
        self.normalizer = normalizer
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()

    def get(self, key: str) -> Optional[CacheEntry]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at and time.time() > entry.expires_at:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return entry

    def put(self, key: str, entry: CacheEntry) -> None:
        if self.max_entries <= 0:
            return
        self._store[key] = entry
        self._store.move_to_end(key)
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)


class DualRouterLLM:
    def __init__(
        self,
        *,
        fast: LLMAdapter,
        full: LLMAdapter,
        policy: Optional[RoutePolicy] = None,
        cache: Optional[ResponseCache] = None,
    ) -> None:
        self.fast = fast
        self.full = full
        self.policy = policy or RoutePolicy()
        self.cache = cache
        self._fast_ready = True

    def start(self) -> AdapterStatus:
        full_status = self.full.start()
        if not full_status.ready:
            return AdapterStatus("DualRouterLLM", False, "full adapter unavailable")
        fast_status = self.fast.start()
        self._fast_ready = bool(fast_status.ready)
        detail = "fast+full" if self._fast_ready else "full-only"
        return AdapterStatus("DualRouterLLM", True, detail)

    def generate(self, request: LLMRequest) -> LLMResponse:
        route = (request.route_hint or self.policy.select_route(request.prompt)).casefold()
        if route == "fast" and not self._fast_ready:
            route = "full"
        adapter = self.fast if route == "fast" else self.full
        key = self._cache_key(route, request) if self.cache and route == "fast" else None
        if key and self.cache:
            cached = self.cache.get(key)
            if cached:
                return LLMResponse(cached.text, cached.tokens, 0.0)
        try:
            response = adapter.generate(request)
        except Exception:
            if route != "fast":
                raise
            response = self.full.generate(LLMRequest(**{**request.__dict__, "route_hint": "full"}))
            route = "full"
            key = None
        if key and self.cache and response.text:
            expiry = time.time() + self.cache.ttl_seconds if self.cache.ttl_seconds > 0 else 0.0
            self.cache.put(key, CacheEntry(response.text, response.tokens, expiry))
        return response

    def stream_chunks(self, request: LLMRequest):
        route = (request.route_hint or self.policy.select_route(request.prompt)).casefold()
        if route == "fast" and not self._fast_ready:
            route = "full"
        adapter = self.fast if route == "fast" else self.full
        stream = getattr(adapter, "stream_chunks", None)
        if callable(stream):
            yield from stream(request)
            return
        response = self.generate(request)
        yield LLMStreamChunk(response.text, True, response.tokens)

    def _cache_key(self, route: str, request: LLMRequest) -> str:
        prompt = self.cache.normalizer(request.prompt) if self.cache and self.cache.normalizer else request.prompt
        payload = f"{route}\0{prompt}\0{request.max_tokens}\0{request.temperature}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
