Awesome. Here’s a **Notion-ready Dev Notes page** you can paste directly into your workspace (or commit as `docs/DEV_NOTES.md`). It’s structured for quick skimming and action, with checkboxes you can tick off as you go.

---

# AutoNotious — Dev Notes & Task Checklist (v1)

## Snapshot (what exists)

* ChatGPT-style UI with **SSE streaming**
* **FastAPI** backend, **LiteLLM** proxy → OpenAI
* **Sessions & messages** persisted (SQLite)
* **Whole-session summarization** (chunked/map-reduce intent)
* **Notion export** (basic Markdown → blocks)
* Env setup documented; local dev workflow working

---

## Top polish wins (most impact per effort)

* [ ] **Standard error envelope** across all endpoints
  `{"error": {"code":"...", "message":"...", "details":{...}, "request_id":"..."}}`
* [ ] **SSE hardening**: heartbeat (`:keepalive\n\n`) every 15–30s; client cancels via AbortController
* [ ] **Retry/backoff**: single retry on transient 5xx with exp. backoff + jitter; never retry 4xx
* [ ] **Token/context safety** for summarization: deterministic chunking when near limits
* [ ] **Notion “upsert”**: store `notion_page_id` per session; create if none, else update children
* [ ] **Session title hygiene**: first user message, ≤80 chars, single line (strip newlines)
* [ ] **“New Chat”**: triggers backend session creation; clears UI state deterministically
* [ ] **Basic session list (read-only)**: left sidebar with recent sessions (title + created\_at)
* [ ] **Observability**: log `request_id`, model, latency, (tokens if available), Notion page URL
* [ ] **Config hygiene**: strict CORS (local only), `.env` never committed, friendly 400 if Notion config missing

---

## API consistency spec (quick reference)

* **Error envelope** (use everywhere):

  * `code` (e.g., `LLM_UPSTREAM_ERROR`, `NOTION_CONFIG_MISSING`)
  * `message` (human-readable)
  * `details` (optional debug context)
  * `request_id` (UUID per request)
* **SSE contract** (`POST /api/chat`):

  * Stream: `data: <content-chunk>\n\n` (multiple)
  * Heartbeat: `:keepalive\n\n` every 15–30s
  * End: `event: end\ndata: done\n\n`
* **Timeouts/limits**:

  * LLM upstream timeout sensible default (e.g., 60s); summarization 120s
  * Max prompt length (server-side guard); truncate with clear message

---

## Summarization spec (fixed shape)

* Output must always include:

  * `# {Title ≤ 80 chars}`
  * `## TL;DR` (1–2 bullets)
  * `## Key Points` (bullets)
  * `## Action Items` (bullets; include “Owner:” / “Due:” only if explicit)
  * `## Notes` (links, code snippets)
* **Chunking (map-reduce)**:

  * Prefer \~3–5 message pairs per chunk (or token heuristic)
  * Summarize each chunk → combine → final pass for consistent sections
* Defaults:

  * Chat model: `gpt-4o-mini`, temp **0.7**
  * Summary model: `gpt-4o-mini`, temp **0.3**

**Tasks**

* [ ] Implement deterministic chunker (by token estimate or message count)
* [ ] Guarantee section headers even when content is sparse
* [ ] Clamp final markdown length (soft cap) to avoid massive pages

---

## Notion export (minimal, reliable)

**Mapping (v1)**

* `# ` → `heading_1`
* `## ` → `heading_2`
* `- ` → `bulleted_list_item`
* fenced \`\`\` → `code` (language “markdown”)
* plain → `paragraph`

**Behavior**

* [ ] On “Save to Notion”: if no summary, **auto-summarize**, then save
* [ ] **Upsert** policy: create page if none; otherwise **replace children** (or append, your call—pick one)
* [ ] Persist `notion_page_id` on the Session

**Failure handling**

* [ ] 400 with hint when `NOTION_API_KEY` or `NOTION_PARENT_PAGE_ID` missing
* [ ] 502 with short message on upstream Notion errors; debug details go to logs

---

## Persistence & sessions

* Tables: **Session**, **Message**, (optional) **Summary**
* Ordering: stable by `created_at`
* Title: derive from first user message; editable later (post-v1)

**Tasks**

* [ ] Verify stable ordering for `/sessions/{id}/messages`
* [ ] Add “New Chat” endpoint or flow; ensure UI resets + new `session_id`
* [ ] (Optional) Add `Summary` table for caching last summary + timestamps

---

## Observability & reliability

**Logging**

* [ ] Include `request_id`, model, total latency, upstream status
* [ ] Log Notion page URL on success; redact secrets from logs

**SSE reliability**

* [ ] Heartbeats to keep connections alive behind proxies
* [ ] Client cancellation (AbortController) cleanly closes server generator

**Retries**

* [ ] Backoff+Jitter: 1 retry on 5xx for LLM/Notion
* [ ] No retry on 4xx (auth/validation)

**(Optional) LiteLLM DB**

* [ ] Enable LiteLLM logging/metrics **if** you want per-session usage insights (mask sensitive content)

---

## Testing plan (what to actually run)

**Unit**

* [ ] Chunker produces predictable pieces; handles edge cases (very short/very long)
* [ ] Summarizer returns all sections even when some are empty
* [ ] Markdown→Notion converter handles: blank lines, nested bullets (flatten safely), unclosed code fences

**Integration**

* [ ] End-to-end: send → stream (≥2 chunks) → persist → summarize → Notion (returns URL)
* [ ] Failures:

  * LLM 5xx → retried once → success/fail surfaces clearly
  * Notion 4xx/5xx → error envelope returned; UI shows actionable message
  * Missing Notion config → 400 with setup hint

**Frontend**

* [ ] Composer: Enter/Shift+Enter, disabled while streaming, **Stop** works
* [ ] Streaming: single assistant bubble grows; auto-scroll stays at bottom
* [ ] Buttons: Save disabled until summary exists (or triggers auto summarize-then-save)
* [ ] Refresh restores current session and messages

---

## Configuration & security

**Env (backend only; never to frontend)**

* `OPENAI_API_KEY`
* `MODEL` (default: `gpt-4o-mini`)
* `LITELLM_URL` (default: `http://localhost:4000/v1/chat/completions`)
* `DATABASE_URL` (default: `sqlite:///./app.db`)
* `NOTION_API_KEY`
* `NOTION_PARENT_PAGE_ID`

**Tasks**

* [ ] CORS: restrict to local frontend origin only
* [ ] `.env` in `.gitignore` (keep only `.env.example` in repo)
* [ ] Startup self-check: on boot, log which integrations are enabled/missing

---

## Roadmap (post-v1 ideas — optional)

* [ ] Session switcher UI with search & delete
* [ ] “Regenerate response” for last prompt
* [ ] Prompt presets & summary presets (e.g., “Action Items only”)
* [ ] Model selection per session (fast vs. accurate)
* [ ] Update existing Notion page sections selectively instead of full replace
* [ ] Basic analytics page (per-session token counts, latency)

---

## Learning checklist (your fastest ramp)

* [ ] **REST mental model** (FastAPI routes, Pydantic models, status codes)
* [ ] **SSE** basics (data frames, heartbeats, cancel)
* [ ] **React** essentials (components, state, props; one page + streaming UI)
* [ ] **LiteLLM proxy** usage (model config, streaming, logging)
* [ ] **Notion block model** (think “structured blocks”, not raw markdown)

---

## Definition of Done (v1)

* [ ] Real-time streaming feels smooth; stop works
* [ ] Sessions persist; refresh is seamless
* [ ] Summaries always include required sections (short & long chats)
* [ ] “Save to Notion” creates/updates a page; user sees a link
* [ ] Errors are actionable; logs are useful; no secrets leak

---

If you want, I can also tailor this into a `CHECKLIST.md` (laser-focused on tasks) or split “Dev Notes” and “API Spec” into two pages—your call.
