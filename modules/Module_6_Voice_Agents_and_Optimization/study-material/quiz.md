# Module 06 — Quiz

<!-- INSTRUCTOR: The quiz-me skill uses these. Answers are here so Claude can check,
     but the rule is Claude NEVER shows them before the learner attempts. Hint first.
     Q6-Q8 cover the bonus optimization material — flag them as bonus when quizzing. -->

## Q1. What two constraints does wrapping a text agent in speech add that a chat UI doesn't have?
- Type: recall
- **Answer:** Turn-taking (detecting when the user has stopped speaking, handling
  interruptions, not talking over them) and a much stricter latency budget (dead air feels
  broken in speech in a way an invisible delay doesn't in chat).
- **Hint:** Think about what a send button does for you that speech can't rely on.

## Q2. Why does turning masking on force streaming off in the cascade architecture?
- Type: explain-why
- **Answer:** Masking requires running the A2A Masker over the *complete* reply before it's
  spoken — you can't scrub PII out of a sentence that's already been spoken aloud. So
  `STREAM_ENABLED = AGENT_RESPONSE_STREAM and not MASK`: with masking on, the reply is
  buffered whole and only then spoken; streaming and masking can't both be on at once.
- **Hint:** Ask what it would mean to "un-speak" a word after masking finds PII in it.

## Q3. In the speech-to-speech architecture, can the A2A Security Judge stop the agent's spoken
reply from playing? Why or why not?
- Type: application
- **Answer:** No. Because the model hears raw audio directly, there's no discrete transcript to
  gate beforehand. The Judge only sees the transcript *after* the Live API finishes
  transcribing it, and it runs **concurrently** with the model's response generation — so by
  the time it flags `BLOCKED`, the model may already be speaking or finished. It's a post-hoc
  warning, not a pre-agent gate.
- **Hint:** Compare when cascade's Judge runs (before the agent) to when S2S's Judge runs
  (relative to the model already hearing the audio).

## Q4. Name one thing the cascade architecture buys you that speech-to-speech can't, and one
thing S2S buys you that cascade can't.
- Type: application
- **Answer:** Cascade buys a real pre-agent security gate and full per-stage observability
  (a Phoenix span per stage) — at the cost of additive latency. S2S buys lower latency and
  much more natural turn-taking (native to the Live API) — at the cost of a weaker, post-hoc
  security guarantee and less per-stage visibility.
- **Hint:** One trades control for speed; name what's gained and lost on each side.

## Q5. Why is a tool call graded deterministically in the benchmark, while a spoken answer is
graded by an LLM judge?
- Type: explain-why
- **Answer:** A tool call (which function, which args) is an objective fact you can check
  exactly. A spoken answer's *phrasing* varies ("$120" vs. "one hundred twenty dollars") even
  when the underlying fact is identical, so an LLM judge is needed to grade meaning rather than
  exact text — and the judge is also shown the actual tool calls, so it can penalize a reply
  that claims an action (e.g. "I've logged your return") that no tool call actually performed.
- **Hint:** One is a fact you can string-match; the other can be phrased many correct ways.

## Q6 (bonus). Quantization drops weight precision from 16/32 bits to 4 bits. Why does that make
the model *faster*, not just smaller?
- Type: explain-why
- **Answer:** Inference at each decode step is memory-bandwidth-bound — it has to move the
  model's weights through memory for every token generated. Fewer bits per weight means less
  data to move per step, so decoding speeds up as a direct consequence of the smaller memory
  footprint, not despite it. The measured numbers show both: ~29.9 GB/~17.6 tok/s at full
  precision vs. ~5.8 GB/~32.5 tok/s at 4-bit.
- **Hint:** Ask what has to physically move through memory on every single generated token.

## Q7 (bonus). Quantizing a model barely changed TTFT (0.084s → 0.073s) but nearly halved ITL
(0.057s → 0.030s). Why did one metric move so much more than the other?
- Type: application
- **Answer:** TTFT is dominated by the **prefill** pass — a compute-bound pass over the *entire*
  prompt at once, done a single time; shrinking the weights doesn't change much there. ITL is
  the cost of each **decode** step afterward, which is memory-bandwidth-bound — moving the same
  cached weights through memory one token at a time, over and over. A smaller model helps that
  repeated, bandwidth-bound cost far more than the one-time compute-bound prefill.
- **Hint:** One happens once over the whole prompt; the other happens once per output token.

## Q8 (bonus). A speculative-decoding draft has a very negative average log-likelihood score
under the main model. What does that predict, and why?
- Type: application
- **Answer:** A very negative score means the main model considered the draft's tokens highly
  unlikely — poor alignment between the draft and main models. In a real implementation, the
  main model would reject most of the draft (regenerating from near the start), so little of
  the draft model's work gets reused — a small or negligible speedup. A score close to 0 would
  predict the opposite: most of the draft accepted, most forward passes skipped, a large speedup.
- **Hint:** Log-probabilities are always ≤ 0 — what does "close to 0" vs. "very negative" say
  about how likely the main model found those tokens?
