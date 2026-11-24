from seniorbot.streaming import StreamingChunk, StreamingConfig, StreamingController


def test_streaming_requires_stable_high_confidence_text() -> None:
    controller = StreamingController(
        StreamingConfig(enabled=True, early_response_min_chars=5, min_stable_updates=2)
    )

    assert not controller.update(StreamingChunk("hello", confidence=0.9)).should_respond
    decision = controller.update(StreamingChunk("hello", confidence=0.9))

    assert decision.should_respond
    assert decision.reason == "early_stable"
