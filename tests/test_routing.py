from seniorbot.contracts import AdapterBase, LLMRequest, LLMResponse
from seniorbot.routing import DualRouterLLM, ResponseCache, RoutePolicy


class FakeLLM(AdapterBase):
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return LLMResponse(f"{self.name}:{request.prompt}")


def test_route_policy_and_bounded_cache() -> None:
    fast, full = FakeLLM("fast"), FakeLLM("full")
    router = DualRouterLLM(
        fast=fast,
        full=full,
        policy=RoutePolicy(fast_max_chars=10),
        cache=ResponseCache(max_entries=2),
    )
    router.start()

    request = LLMRequest(prompt="short", max_tokens=20, temperature=0.2)
    first = router.generate(request)
    second = router.generate(request)

    assert first.text == second.text
    assert fast.calls == 1
    assert full.calls == 0

    router.generate(LLMRequest(prompt="long prompt that exceeds the fast route threshold", max_tokens=20))
    assert full.calls == 1
