"""Explicit dialogue state with bounded, inspectable turn history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class DialogueTurn:
    user_text: str
    response_text: str
    route: str = "default"
    latency_seconds: float = 0.0
    audio_path: str = ""


@dataclass
class DialogueState:
    """Conversation state; persistence is deliberately an application concern."""

    max_turns: int = 8
    turns: list[DialogueTurn] = field(default_factory=list)
    last_response: str = ""

    def add_turn(self, turn: DialogueTurn) -> None:
        self.turns.append(turn)
        self.last_response = turn.response_text
        if self.max_turns > 0:
            del self.turns[:-self.max_turns]

    def clear(self) -> None:
        self.turns.clear()
        self.last_response = ""

    def prompt_context(self) -> str:
        lines: list[str] = []
        for turn in self.turns:
            lines.append(f"User: {turn.user_text}")
            lines.append(f"Assistant: {turn.response_text}")
        return "\n".join(lines)

    def extend(self, turns: Iterable[DialogueTurn]) -> None:
        for turn in turns:
            self.add_turn(turn)
