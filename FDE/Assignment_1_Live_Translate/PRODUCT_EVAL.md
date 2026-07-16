# Product Evaluation — Live Translate

- **Student:** Jorge Alvarez
- **Date:** 2026-07-16
- **Video demo:** _PENDING — record 60–90s before submitting_
- **LLM provider / model:** Anthropic · `claude-sonnet-4-6`
- **Backend target:** local gateway `http://localhost:8787` (auto rubric) · deployed gateway `https://jorge-livetranslate-gw.fly.dev` (live-site test)

## Verdict

> This is shippable. The product translates arbitrary English web pages into natural
> Mexican Spanish end to end, through a clean two-service split (public Node gateway →
> private Python AI service) deployed on Fly.io, with a two-tier cache that makes repeat
> text effectively free. The strongest part is the cache: a hit returns in single-digit
> milliseconds versus a ~2.3 s LLM miss (≈300×), it survives a restart from SQLite on a
> Fly volume (verified in production), and the key never touches the browser-facing edge.
> The weakest part is cold whole-page latency on a large first-time page (one LLM call per
> unique string, rate-limited by the provider) — mitigated with concurrent batching, but
> still the main thing a first-time visitor to a big page feels.

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual, grader-assessed)

## 1. Performance & cost (from `benchmark/bench.py`, cold-cache run → `benchmark/_bench.json`)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 7.7 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 2257 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 75.0 % | ≥ 60 % | ✅ |
| Throughput (warm) | 1397 req/s | ≥ 20 | ✅ |
| Error rate | 0.0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.000156 | — | — |
| Monthly savings from cache | $58.67 | — | — |

`python benchmark/bench.py` exits `0` — all SLAs met. Cost model uses the placeholder
prices in `sla.json` ($3 / $15 per Mtok in/out), which are close to current Sonnet rates;
at 500k translations/month the cache cuts the projected bill from ~$78 to ~$20.

## 2. Live-website test

- **Site tested:** `https://www.homedepot.com`, real product pages (RYOBI jobsite fan, RYOBI battery/charger kit) on a strict-CSP e-commerce site I don't control.
- **Backend used:** the **deployed** gateway `https://jorge-livetranslate-gw.fly.dev`, via the Chrome extension. Verified it hit production, not localhost: with the local backend stopped, a single page translate moved the production cache from 5 → 211 requests and 6 → 203 stored rows.
- **Translated whole page?** Yes. Headings, breadcrumbs, nav, product titles, descriptions, and promo copy flipped to Mexican Spanish; layout intact.
- **Coverage gaps:** Text baked into promotional **images** (e.g. the "FREE GOOD INCLUDED" badge graphic) stays English (rasterized, not DOM text). That's an expected limitation of a DOM text-node translator.
- **Cache on re-translate:** Restore → Translate again returns the whole page from cache: hit badges light up and latency collapses to near-zero (cold full-page ≈ 56 s with concurrent batching; warm ≈ instant).
- **Resilience:** Strict CSP did **not** block the extension (content-script injection, not console paste; the console loader would be blocked here). No console errors, no layout breakage. Concurrent batching cut cold whole-page time from ~283 s (sequential) to ~56–63 s.
- **Screenshots:** before/after attached to the video submission.

### Sample translations (observed live on homedepot.com)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| Power Tools | Herramientas eléctricas | n/a | ✅ |
| Jobsite Fans | Ventiladores para obra | n/a | ✅ |
| Add to cart | Agregar al carrito | n/a | ✅ |
| Best Seller | Más vendido | n/a | ✅ |
| ONE+ 18V HP Brushless Cordless Hybrid 9 in. WHISPER SERIES Oscillating Fan (Tool Only) | ONE+ 18V HP Brushless Inalámbrico Híbrido Ventilador Oscilante WHISPER SERIES de 9 pulg. (Solo Herramienta) | ✅ "18V", "9 in." | ✅ |
| $139.00 / $89.00 / $158.00 | $139.00 / $89.00 / $158.00 | ✅ prices verbatim | ✅ |
| Save $69.00 (44%) | Guardar $69.00 (44%) | ✅ | ✅ |
| Model #PBLHF01B · Store SKU #1014835246 | Modelo #PBLHF01B · N° de SKU de la tienda 1014835246 | ✅ codes verbatim | ✅ |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | Pass | Full homedepot product pages read naturally; no mistranslations in the sampled set |
| Mexican-Spanish register (es-MX) | Pass | "Agregar al carrito", "computadora"-style Mexican vocabulary; prompt explicitly pins es-MX over Castilian |
| Numbers / prices / codes preserved | Pass | `$139.00`, `$89.00`, `Guardar $69.00 (44%)`, `Modelo #PBLHF01B`, `SKU 1014835246` all verbatim |
| Page coverage | Partial | All DOM text translated; text inside promo images stays English (rasterized, out of scope) |
| Cache effectiveness | Pass | Two-tier (memory + SQLite); hit ≈300× faster than miss; survives restart from Fly volume (verified in prod: restart → still `cached:true`, served from `db_hits`) |
| Latency vs SLA | Pass | `bench.py` exits 0; hit p95 7.7 ms, miss p95 2257 ms, throughput 1397 req/s |
| Error handling (no silent English) | Pass | LLM failure propagates → gateway returns `502`; no try/except returns the input; `400` on bad input, `501` mapped |
| Resilience on a real site | Pass | Works on strict-CSP homedepot.com via the extension; no breakage; concurrent batching keeps cold pages tolerable |
| UX polish | Pass | One-click translate/restore; live progress counter; cache-hit badges; instant on re-translate |

**Observability:** one request is greppable end-to-end across both services by a single ID.
For example, `requestId: EVAL-TRACE-e56460` appears in both `gateway.log` and `ai-service.log`.
The gateway reuses an inbound `X-Request-Id` or mints one and forwards it to the AI service.

## 4. Top fixes before shipping

1. **Cold whole-page latency.** A large first-time page is one LLM call per unique string, capped by the provider's rate limit. Concurrent batching (implemented, with in-batch dedup) helps; next levers are a shared warm cache across users (already global by design) and streaming results into the DOM as each batch lands.
2. **Cost prices are placeholders.** Pin `sla.json` `input_usd_per_mtok` / `output_usd_per_mtok` to Anthropic's exact published rates before trusting the dollar figures.
3. **Image text is untranslated.** Out of scope for a DOM translator, but worth noting for a real product (would need OCR or server-side rendering).

---

### Engineering notes (for the grader)

- **Provided-file change — authorized.** `widget/translation-widget.js` and its extension copy
  carry a small fix to a **race condition in the provided extension**: `content.js` sets the
  saved backend URL from `chrome.storage` in an async callback that fires *after* the widget
  captures its URL synchronously, so the widget always fell back to `localhost:8787` and could
  never reach a deployed gateway. The fix resolves `API_URL` lazily at request time (course
  PR #60; the instructor authorized committing this fix on the course Slack). Without it, the
  "extension works against the public gateway" requirement is unreachable.
- **Hygiene:** no secrets, `node_modules/`, `.venv/`, `*.db`, or `*.log` staged. The Anthropic
  key lives only in `.env` (git-ignored) locally and as a Fly secret in production.
- **Deploy shape:** gateway public on Fly; AI service private (no public IP, reached only over
  Fly's internal network), so the key never sits on the browser-facing edge. SQLite cache on a
  Fly volume for restart survival.

### Stretch goals delivered (beyond the required brief)

- **Concurrent + deduped batch translation.** `/translate/batch` translates unique strings in
  parallel (bounded, with provider-backoff) and de-dupes within the batch so the same text is
  never sent to the LLM twice. Cut a cold full-page homedepot translate from ~283 s to ~56 s.
- **`docker-compose.yml`.** `docker compose up --build` runs both services; only the gateway is
  host-published, the AI service stays internal.
- **Language picker.** es-MX · es-ES · pt-BR · fr-FR, threaded through the `target` contract and
  selectable in the extension popup. Verified in production — e.g. "Add to cart" → "Agregar al
  carrito" (es-MX) vs "Añadir al carrito" (es-ES), real register control. Known nuance: for
  fr-FR the model localizes the price format (`$19.99` → `19,99 $`); the graded es-MX target
  preserves prices verbatim.
