from __future__ import annotations

from seniorbot.contracts import AdapterBase, AdapterStatus, LLMResponse, STTResult, TTSResult
from seniorbot.pipeline import VoicePipeline


class FakeASR(AdapterBase):
    def transcribe(self, audio_path: str) -> STTResult:
        assert audio_path == "fixture-audio"
        return STTResult("hello from audio", confidence=0.95)


class FakeLLM(AdapterBase):
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return LLMResponse("A concise response.", tokens=3)


class FakeTTS(AdapterBase):
    def __init__(self) -> None:
        self.texts = []

    def synthesize(self, text: str) -> TTSResult:
        self.texts.append(text)
        return TTSResult(audio_path="fixture-output")


def test_text_pipeline_tracks_dialogue_and_calls_tts() -> None:
    asr, llm, tts = FakeASR(), FakeLLM(), FakeTTS()
    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)
    statuses = pipeline.start()

    turn = pipeline.handle_text("Please summarize this sentence.")

    assert all(isinstance(status, AdapterStatus) for status in statuses)
    assert turn.response_text == "A concise response."
    assert turn.audio_path == "fixture-output"
    assert pipeline.dialogue.last_response == "A concise response."
    assert len(llm.requests) == 1
    assert llm.requests[0].prompt.endswith("User: Please summarize this sentence.")


def test_audio_entry_point_stays_inside_the_same_text_pipeline() -> None:
    asr, llm, tts = FakeASR(), FakeLLM(), FakeTTS()
    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)

    turn = pipeline.handle_audio("fixture-audio")

    assert turn.user_text == "hello from audio"
    assert len(llm.requests) == 1


def test_urgent_policy_path_does_not_call_llm() -> None:
    asr, llm, tts = FakeASR(), FakeLLM(), FakeTTS()
    pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)

    turn = pipeline.handle_text("This is an emergency")

    assert turn.route == "policy"
    assert llm.requests == []
    assert tts.texts == [turn.response_text]
