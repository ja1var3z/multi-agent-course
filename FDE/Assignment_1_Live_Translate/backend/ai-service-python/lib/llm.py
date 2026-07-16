"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from anthropic import AsyncAnthropic

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")

# Lazy singleton: created on first call, after load_dotenv() has run,
# and reused across requests (the SDK client keeps a connection pool).
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        # max_retries lets the SDK ride out transient 429 (rate-limit) and 5xx
        # bursts with exponential backoff — important once we translate a batch
        # concurrently. A real, persistent failure still raises → the caller 502s.
        _client = AsyncAnthropic(max_retries=5, timeout=30.0)  # reads ANTHROPIC_API_KEY
    return _client


# Register descriptions per locale — keeps translation faithful to how the
# language is actually spoken in that region (Claude handles any target; these
# just pin the register for the ones the picker offers).
_REGISTERS = {
    "es-MX": (
        "natural MEXICAN Spanish (es-MX) — the everyday register used in Mexico, "
        "not Castilian Spanish. Prefer Mexican vocabulary (e.g. 'computadora', "
        "'carro', 'ustedes' instead of 'vosotros')"
    ),
    "es-ES": (
        "natural Castilian Spanish (es-ES) as used in Spain — use 'vosotros' and "
        "Spain vocabulary (e.g. 'ordenador', 'coche', 'móvil')"
    ),
    "pt-BR": "natural Brazilian Portuguese (pt-BR) as spoken in Brazil",
    "fr-FR": "natural French (fr-FR) as used in France",
    "de-DE": "natural German (de-DE)",
}


def _system_prompt(target: str) -> str:
    register = _REGISTERS.get(target, f"the language/locale '{target}'")
    return (
        f"You are a professional translator. Translate the user's English text into {register}. "
        "Return ONLY the translation — no preamble, no notes, no wrapping quotes. "
        "Keep numbers, prices ($), SKUs, and product/model codes exactly as written. "
        "If the input is a short UI label, translate it as a UI label."
    )


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default).

    FAIL LOUD: provider errors propagate to the caller (which answers 502).
    """
    msg = await _get_client().messages.create(
        model=model,
        max_tokens=1024,
        system=_system_prompt(target),
        messages=[{"role": "user", "content": text}],
    )
    out = msg.content[0].text.strip()
    # strip a matching pair of wrapping quotes the model may add
    for open_q, close_q in (('"', '"'), ("“", "”"), ("'", "'")):
        if len(out) >= 2 and out.startswith(open_q) and out.endswith(close_q):
            out = out[1:-1].strip()
            break
    return out
