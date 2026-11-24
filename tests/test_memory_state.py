from seniorbot.memory import MemoryState


def test_memory_search_and_explicit_promotion() -> None:
    state = MemoryState(max_entries=4)
    record = state.remember("Edge pipeline uses bounded memory", importance=0.8)

    results = state.search("bounded memory")

    assert results[0]["record_id"] == record.record_id
    assert state.promote(record.record_id, "mtm")
    assert state.get(record.record_id).level == "mtm"


def test_hidden_memory_is_not_retrieved_and_forget_is_explicit() -> None:
    state = MemoryState()
    hidden = state.remember("do not retrieve", metadata={"hidden": True})
    visible = state.remember("retrieve this design note")

    assert all(item["record_id"] != hidden.record_id for item in state.search("retrieve"))
    assert state.forget(visible.record_id)
    assert state.get(visible.record_id) is None
