# Seniorbot

Seniorbot is a hardware-agnostic voice-assistant core shaped for a Jetson-class
edge device and an s6-rc based runtime. The public export keeps the reusable
architecture and deterministic text tests separate from the hardware lab.

## Architecture

```text
Hardware integration: capture audio and provide its path
  -> VoicePipeline.handle_audio
       |-- ASR adapter -> transcribed text
       |-- Text policy, DialogueState and MemoryState
       |-- LLM adapter (optional fast/full routing)
       +-- TTS adapter -> synthesized audio path
Hardware integration: play the synthesized audio
```

- `seniorbot/contracts.py` defines stable ASR, LLM, TTS, and lifecycle data contracts.
- `seniorbot/adapters.py` isolates model and hardware implementations behind protocols.
- `seniorbot/pipeline.py` owns the text boundary and the ASR-to-LLM-to-TTS orchestration.
- `seniorbot/dialogue.py` keeps bounded turn state; `seniorbot/memory.py` provides explicit STM/MTM/LTM-style state and conservative retrieval without implicit disk writes.
- `seniorbot/routing.py` implements deterministic fast/full model routing and a bounded in-memory response cache.
- `services/full-s6/` contains the minimal s6-rc service contract and dependency graph.

## Jetson-edge pipeline

The intended edge flow is capture, speech recognition, policy evaluation,
bounded context assembly, local model generation, speech synthesis, and
playback. Each hardware or model implementation is replaceable through an
adapter. Policy responses can terminate the model path deterministically for
high-risk markers.

The Full-s6 example demonstrates service lifecycle and dependency ordering.
The readiness oneshot exits successfully, the voice longrun emits a status
record and waits for a shutdown signal, and the online bundle composes both.
The example uses placeholder services for audio readiness and voice processing.
Device drivers, model weights, network setup, recordings, and deployment
secrets stay in the hardware lab.

## Text tests and hardware lab

The tests use in-process adapter doubles. They validate routing, dialogue state,
memory retrieval, confidence-gated streaming, and the complete text pipeline
without a microphone, speaker, model download, network service, or audio file.
Hardware acceptance belongs to a separate lab gate and should never be inferred
from a green text-only test run.

With Python 3.10 or newer and pytest installed, run the suite from this directory.

```bash
python3 -m pytest -q -p no:cacheprovider
```

Expected result: `7 passed`.

## Publication boundary

This export intentionally contains no Wi-Fi data, local addresses, SSH material,
API credentials, recordings, personal lists or memories, private paths, email
addresses, runtime caches, model weights, or device reports.

## License

MIT. See [LICENSE](LICENSE).
