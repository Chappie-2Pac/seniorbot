# Seniorbot

[![CI](https://github.com/Chappie-2Pac/seniorbot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Chappie-2Pac/seniorbot/actions/workflows/ci.yml)

## A deterministic voice-assistant core for local edge AI

Seniorbot is a hardware-agnostic Python core for voice assistants that combine
automatic speech recognition, dialogue state, local language models, text-to-
speech, bounded memory, and explicit safety policy.

The project demonstrates how I design an AI product as a set of replaceable,
testable contracts instead of one tightly coupled hardware application.

The [Seniorbot portfolio case study](https://werkstatt-core.ludwig-grosse484994.chatgpt.site/seniorbot)
shows the wider local edge-AI integration story and the runtime evidence around
this public core.

## Architecture

```text
audio input
    -> ASR adapter
    -> text policy and bounded dialogue state
    -> deterministic fast/full LLM routing
    -> bounded memory context
    -> TTS adapter
    -> audio output
```

The pipeline is implemented in `seniorbot/pipeline.py`. ASR, LLM, and TTS
integrations are defined by protocols in `seniorbot/adapters.py`; the core can
therefore be tested with in-process doubles and connected to real hardware or
model services at the integration boundary.

## What I built here

- Stable contracts for ASR, LLM, TTS, lifecycle, readiness, and streaming.
- A `VoicePipeline` with explicit text and audio boundaries.
- Bounded dialogue and memory state with conservative retrieval.
- Explicit memory promotion, retrieval, and deletion operations.
- Deterministic fast/full model routing and an in-memory response cache.
- Confidence-gated streaming decisions for incremental ASR results.
- Policy decisions that can terminate or prefix a model response before model
  execution.
- An s6-rc service topology for readiness, voice processing, and online bundle
  ownership.
- A text-first test suite that validates the system without microphone,
  speaker, model download, network service, or audio recording.

## Quickstart

Python 3.10 or newer is supported.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pytest
python -m pytest -q -p no:cacheprovider
```

The current suite covers routing, dialogue state, bounded memory, streaming,
policy decisions, and the complete text pipeline.

Connect concrete adapters through the stable pipeline contract:

```python
from seniorbot.pipeline import VoicePipeline

pipeline = VoicePipeline(asr=asr_adapter, llm=llm_adapter, tts=tts_adapter)
pipeline.start()
turn = pipeline.handle_text("Summarize the latest system status.", route_hint="fast")
print(turn.response_text)
```

## Project layout

| Path | Responsibility |
|---|---|
| `seniorbot/contracts.py` | ASR, LLM, TTS, lifecycle, and streaming contracts |
| `seniorbot/adapters.py` | Replaceable integration protocols |
| `seniorbot/pipeline.py` | End-to-end orchestration from text/audio input to TTS output |
| `seniorbot/dialogue.py` | Bounded conversation state |
| `seniorbot/memory.py` | Explicit STM/MTM/LTM-style memory state and retrieval |
| `seniorbot/routing.py` | Fast/full model routing and response caching |
| `seniorbot/policy.py` | Deterministic safety decisions |
| `services/full-s6/` | Minimal s6-rc lifecycle and dependency contract |
| `tests/` | In-process adapter and pipeline verification |

## Engineering value

Seniorbot is a strong example of edge-AI systems engineering: the model is
replaceable, hardware is isolated behind adapters, state is bounded, and every
important boundary can be tested independently. Device drivers, model
weights, recordings, and deployment configuration belong in the integration
environment, keeping the core portable and reviewable.

## License

MIT. See [`LICENSE`](LICENSE).
