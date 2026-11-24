"""Hardware-agnostic ASR -> dialogue -> LLM -> TTS orchestration."""

from __future__ import annotations

import time

from .adapters import ASRAdapter, LLMAdapter, TTSAdapter
from .contracts import AdapterStatus, LLMRequest, STTResult, TTSResult
from .dialogue import DialogueState, DialogueTurn
from .memory import MemoryState
from .policy import SafetyPolicy


class VoicePipeline:
    def __init__(
        self,
        *,
        asr: ASRAdapter,
        llm: LLMAdapter,
        tts: TTSAdapter,
        dialogue: DialogueState | None = None,
        memory: MemoryState | None = None,
        policy: SafetyPolicy | None = None,
        system_prompt: str = "You are a concise, helpful local assistant.",
    ) -> None:
        self.asr = asr
        self.llm = llm
        self.tts = tts
        self.dialogue = dialogue or DialogueState()
        self.memory = memory or MemoryState()
        self.policy = policy or SafetyPolicy()
        self.system_prompt = system_prompt

    def start(self) -> list[AdapterStatus]:
        statuses = [self.asr.start(), self.llm.start(), self.tts.start()]
        failed = [status for status in statuses if not status.ready]
        if failed:
            names = ", ".join(status.name for status in failed)
            raise RuntimeError(f"adapter readiness failed: {names}")
        return statuses

    def handle_audio(self, audio_path: str, *, route_hint: str | None = None) -> DialogueTurn:
        return self.handle_stt(self.asr.transcribe(audio_path), route_hint=route_hint)

    def handle_stt(self, result: STTResult, *, route_hint: str | None = None) -> DialogueTurn:
        return self.handle_text(result.text, route_hint=route_hint)

    def handle_text(self, user_text: str, *, route_hint: str | None = None) -> DialogueTurn:
        started = time.perf_counter()
        normalized = (user_text or "").strip()
        if not normalized:
            response_text = "I did not receive any text. Please try again."
            route = "policy"
        else:
            decision = self.policy.evaluate(normalized)
            if decision.response_override:
                response_text = decision.response_override
                route = "policy"
            else:
                prompt = self._build_prompt(normalized)
                response = self.llm.generate(
                    LLMRequest(
                        prompt=prompt,
                        max_tokens=256,
                        temperature=0.2,
                        system_prompt=self.system_prompt,
                        route_hint=route_hint,
                    )
                )
                response_text = f"{decision.response_prefix or ''}{response.text.strip()}".strip()
                route = route_hint or "default"
        audio: TTSResult = self.tts.synthesize(response_text)
        turn = DialogueTurn(
            user_text=normalized,
            response_text=response_text,
            route=route,
            latency_seconds=time.perf_counter() - started,
            audio_path=audio.audio_path,
        )
        self.dialogue.add_turn(turn)
        return turn

    def _build_prompt(self, user_text: str) -> str:
        context = self.dialogue.prompt_context()
        memories = self.memory.search(user_text, limit=3)
        memory_lines = "\n".join(f"- {item['snippet']}" for item in memories)
        sections = [self.system_prompt]
        if context:
            sections.append(f"Conversation:\n{context}")
        if memory_lines:
            sections.append(f"Relevant explicit memory:\n{memory_lines}")
        sections.append(f"User: {user_text}")
        return "\n\n".join(sections)
