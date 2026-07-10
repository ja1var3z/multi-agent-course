# Module 06 — Key Concepts (Glossary)

<!-- INSTRUCTOR: Short, accurate definitions Claude uses to stay precise.
     The explain-eli5 skill reads from here to simplify without becoming wrong. -->

- **Voice agent** — A text agent (same ADK agent, MCP tools, Mem0 memory as Module 5) wrapped
  in speech-to-text on input and text-to-speech on output.
- **STT / TTS** — Speech-to-text (audio → transcript) and text-to-speech (text → spoken audio),
  the two conversions that sit around a voice agent's text pipeline.
- **Turn-taking** — Deciding when a speaker has finished, handling interruptions, and not
  talking over the user — a constraint speech has that a chat UI (send button) doesn't.
- **Latency budget** — The time a pause can last before it *feels* broken; much stricter for
  speech (dead air) than for chat (an invisible delay).
- **Cascade architecture** — Discrete, separately-owned stages: STT → sanitize → A2A Security
  Judge → ADK agent (+MCP tools, Mem0) → A2A Masker → TTS. Latency is additive across stages;
  the Judge is a full pre-agent gate.
- **Speech-to-speech (S2S)** — One multimodal model (Gemini Live) takes audio in and emits audio
  out directly, calling tools inline; no separate STT/TTS stages to inspect.
- **Gemini Live / `run_live()`** — ADK's bidirectional-streaming mode
  (`RunConfig(streaming_mode=BIDI, response_modalities=["AUDIO"])`) that drives the S2S agent.
- **Post-hoc / concurrent guardrail** — S2S's security check: the Judge evaluates the finished
  transcript *while* the model is already generating its spoken reply, so it can flag a turn
  after the fact but cannot block the audio already playing.
- **Streaming/masking interlock** — Cascade's rule `STREAM_ENABLED = AGENT_RESPONSE_STREAM and
  not MASK`: masking a reply requires buffering it whole (can't mask what's already being
  spoken), so masking and sentence-level streaming can't both be on.
- **Tool accuracy (precision)** — Of the tool calls the agent made, how many were the right
  tool with the right args — graded deterministically.
- **Tool recall** — Of the tool calls the agent *should* have made, how many actually fired —
  graded deterministically.
- **Response accuracy (precision)** — Of what the agent said, how much was correct, including
  not claiming an action it never took — graded by an LLM judge (phrasing varies; facts don't).
- **Response completeness (recall)** — Of the information/actions the answer required, how much
  it actually conveyed or did — graded by an LLM judge.
- **WER (word error rate)** — STT's recognition error rate: transcript vs. the actual spoken text.
- **Hop** — A dependent tool call on the critical path (excluding the always-on
  `search_memory`). 1 hop = one lookup; 2 hops = a second call that depends on the first
  call's result (e.g. "cancel my most recent order" = list orders → find newest id → log it).
- **Mean ± std (3 repeats)** — The benchmark's answer to sampled, non-deterministic models: run
  each query 3× so the *conclusion* reproduces even though individual scores wobble.
- **Quantization** — Storing model weights in fewer bits (e.g. 4 instead of 16/32) to cut memory
  and, often, increase speed, via `bitsandbytes` (`load_in_4bit=True` / `BitsAndBytesConfig`).
- **FP4 / NF4** — Two 4-bit quantization types; NF4 ("Normal Float 4," from the QLoRA paper) is
  tuned to how neural-network weights are actually distributed.
- **KV cache** — Stored key/value attention projections for already-processed tokens, reused so
  each new token only attends to the cache instead of recomputing all of history.
- **TTFT / ITL / throughput** — Time-to-first-token (dominated by the compute-bound prefill
  pass), inter-token latency (the memory-bandwidth-bound cost of each decode step), and tokens
  generated per second.
- **Speculative decoding** — A small, fast draft model proposes several tokens ahead; the large
  model verifies the whole span in one parallel pass and accepts the correct prefix, regenerating
  only from the first mismatch.
- **Draft model / main model** — The fast, less-accurate proposer and the slow, accurate
  verifier in speculative decoding.
- **Log-likelihood verification score** — The draft's average log-probability under the main
  model; closer to 0 means better alignment (more accepted, bigger speedup), more negative means
  poorer alignment.
