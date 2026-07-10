# Module 6 — Voice Agents & Optimization

The final module is built around **voice agents**: how a text agent becomes a spoken one,
the two architectures for doing it (cascade vs. speech-to-speech), and how to benchmark them
honestly on cost, latency, and capability.

It also ships two **bonus** deep-dives into **LLM optimization** — the inference-level
techniques (quantization, KV caching, speculative decoding) that make any agent, voice or
not, cheaper and faster to run. These are optional: they're *why* a production voice agent's
latency and cost numbers land where they do, but you can skip them and still finish the module.

---

## What's in this module

| Folder | What it covers |
|:--|:--|
| [`study-material/`](study-material/) | The conceptual companion — `lesson.md`, `key-concepts.md`, `exercises.md`, `quiz.md`, `recap-and-preview.md`. |
| [`advance-customer-support-agent-feature-A2A-MCP-ADK_cascading`](advance-customer-support-agent-feature-A2A-MCP-ADK_cascading/) | **Cascade voice agent** — STT → sanitize → A2A judge (gate) → ADK agent (+MCP tools, Mem0) → TTS. A pipeline of separately-owned stages. |
| [`advance-customer-support-agent-feature-A2A-MCP-ADK-s2s`](advance-customer-support-agent-feature-A2A-MCP-ADK-s2s/) | **Speech-to-speech voice agent** — Gemini Live, native audio in/out, tools via function calling, judge as a concurrent monitor. One model instead of a pipeline. |
| [`benchmarking_voice_agents`](benchmarking_voice_agents/) | **Cascade vs. S2S benchmark** — runs the *same* agent through both architectures on 15 audio queries and compares cost, latency, and agentic capability. |
| [`Quantization_and_KV_Caching`](Quantization_and_KV_Caching/) 🎁 | **Bonus — 4-bit quantization** with bitsandbytes + Transformers; TTFT / inter-token latency / throughput measurement; full-precision vs. quantized comparison. |
| [`Speculative_Decoding_from_scratch`](Speculative_Decoding_from_scratch/) 🎁 | **Bonus — speculative decoding** — a small draft model proposes tokens, a large model verifies them in parallel. Built from scratch to show the accept/reject mechanics. |

> **Note:** Like Module 5, this module is taught primarily through its hands-on projects — the
> two capstone variants and the benchmark *are* the lesson. The conceptual companion lives in
> [`study-material/`](study-material/): read `lesson.md` for the concepts (cascade vs. S2S,
> the benchmark's metrics, and the bonus optimization techniques), then go run the projects
> below. `exercises.md` and `quiz.md` work directly off the actual source files referenced above.

---

## Part 1 — Voice agents

A voice agent is a text agent wrapped in **speech-to-text (STT)** on the way in and
**text-to-speech (TTS)** on the way out. The interesting design question is *where the
intelligence lives*, and there are two answers this module contrasts head-to-head:

- **Cascade** — discrete stages, each independently owned and swappable: STT → sanitize →
  security gate → agent (with tools + memory) → TTS. Maximum control and observability;
  latency is the *sum* of the stages.
- **Speech-to-speech (S2S)** — a single multimodal model (Gemini Live) takes audio in and
  emits audio out, calling tools inline. Lower latency and more natural turn-taking; less
  control over each stage, and the security judge has to run as a concurrent monitor rather
  than an in-line gate.

Both agents share the same tools, database, and memory (Mem0) — so the `benchmarking_voice_agents`
harness can isolate the *architecture* as the only variable. It grades four quality axes
(tool precision/recall, response accuracy/completeness) plus STT word-error-rate, latency
(time-to-first-audio and time-to-finish), cost, and PII leaks.

**Concepts:** STT → LLM → TTS pipeline, turn-taking, latency budgeting, cascade vs. S2S
trade-offs, benchmarking voice systems.

## Part 2 (bonus) — LLM optimization

> **Bonus material — optional.** These two folders are self-contained deep-dives for the
> curious; they aren't required to complete the voice-agent work above.

Everything above is bottlenecked by inference speed and memory. Three techniques attack that:

- **Quantization** — store weights in 4 bits instead of 16/32. `Quantization_and_KV_Caching`
  shows a Llama-3.1-8B going from ~30 GB to ~6 GB of VRAM with *higher* throughput.
- **KV caching** — reuse the attention keys/values from prior tokens instead of recomputing
  them every step (covered alongside the streaming/inference notebooks).
- **Speculative decoding** — a cheap draft model guesses several tokens ahead; the big model
  verifies them in one parallel pass and accepts the correct prefix. Multiple tokens per
  expensive forward pass instead of one.

**Concepts:** quantization (FP4 vs. NF4), TTFT / inter-token latency / throughput, KV
caching, draft-and-verify speculative decoding.

---

## Getting started

Each subfolder is self-contained with its own `README.md` and `requirements.txt`:

- **Voice agents** — start with `advance-customer-support-agent-feature-A2A-MCP-ADK_cascading`
  (`./run.sh setup` provisions the conda env, Postgres, seed data, and `.env`), then run the
  `-s2s` variant, then compare them with `benchmarking_voice_agents/reproduce.py`.
- **Optimization (bonus)** — open the notebooks in `Quantization_and_KV_Caching` and
  `Speculative_Decoding_from_scratch`. A GPU (the READMEs benchmark on an NVIDIA A40 via
  RunPod) is recommended for the quantization and speculative-decoding runs.
