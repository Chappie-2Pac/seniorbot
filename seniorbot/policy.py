"""Fail-safe response policy for the text orchestration boundary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    response_override: str | None = None
    response_prefix: str | None = None
    reason: str = "allowed"


class SafetyPolicy:
    """Keep high-risk response paths deterministic and reviewable."""

    def __init__(self) -> None:
        self._urgent_markers = {"emergency", "urgent", "notfall", "notruf"}
        self._medical_markers = {"dose", "dosage", "medication", "medikament"}

    def evaluate(self, user_text: str) -> PolicyDecision:
        lowered = (user_text or "").casefold()
        if any(marker in lowered for marker in self._urgent_markers):
            return PolicyDecision(
                response_override="This sounds urgent. Please contact local emergency services or a trusted person now.",
                reason="urgent_marker",
            )
        if any(marker in lowered for marker in self._medical_markers):
            return PolicyDecision(
                response_prefix="I cannot make medical decisions. Please follow your clinician's instructions. ",
                reason="medical_marker",
            )
        return PolicyDecision()
