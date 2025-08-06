Local Chat App (ChatGPT-Style) + Notion Session Summaries — PRD & API Spec (v1)
1) Overview

    Goal: Local web app with ChatGPT-like chat UX, streaming via LiteLLM → OpenAI, persistent sessions, whole-session summary to Notion (basic Markdown → Notion blocks).

    Out of scope (v1): research tools, web browsing, image generation, Notion databases/tables, auth/multi-user, cloud deploy.

    Success criteria:

        Streaming feels responsive.

        Summary always returns structured Markdown (fixed sections).

        One click creates a readable Notion page.

2) Persona & Top User Stories

    Primary persona: Developer/PM working locally; wants ChatGPT UX + durable notes in Notion.

    User stories (must-have):

        Start a new session, send a prompt, see assistant response streaming.

        Refresh and continue same session (history persists).

        Click Summarize session → get structured Markdown.

        Click Save to Notion → create Notion page under configured parent.

        Clear errors and ability to retry on failures.

3) Defaults (Finalized Decisions)

    Notion flow: If no summary exists when “Save to Notion” is clicked, auto-summarize and then save.

    Session UI: Single active session UI in v1 (backend supports multiple; simple switcher later).

    Regenerate response: Not included in v1.

    Models & params:

        Chat: gpt-4o-mini, temperature 0.7, top_p 1.0.

        Summarization: gpt-4o-mini, temperature 0.3, top_p 1.0.

    History trimming: For chat, keep last ~5k tokens worth of turns in context (truncate older). For summarization, use chunked map-reduce.

    Streaming: SSE from backend to frontend; stop/resume supported.

4) UX Requirements

    Layout: Single-page center column, ChatGPT-style.

    Header: Session title (auto; read-only in v1), buttons: New Chat, Summarize, Save to Notion.

    Message list: Chronological bubbles; auto-scroll to newest.

    Composer: Multiline; Enter = send, Shift+Enter = newline; disabled during streaming; Stop generating button visible while streaming.

    Feedback: Toasters/banners for success (summary created, Notion saved with link) and failures.

    Accessibility: Keyboard focus states; readable contrast. Desktop first.

5) Functional Requirements
5.1 Frontend (React, TypeScript)

    Create/restore current session on load.

    Send message → open SSE stream → render tokens live in a single assistant bubble.

    Summarize button → call summary API; store returned title + markdown (optional preview).

    Save to Notion button → call Notion API (auto-summarize first if needed); show link.

    Error states must release UI (no stuck spinners).

5.2 Backend (FastAPI)

    Persist user message before LLM call.

    Stream assistant tokens back via SSE; persist final assistant message.

    Summarize entire session (chunked if long) to fixed-section Markdown.

    Convert Markdown → Notion blocks (basic mapping) and create page under parent.

    Health endpoint for sanity checks.

6) System Architecture

    Frontend SPA: React (Vite, TS); SSE client; local state + fetch calls.

    FastAPI Backend: chat streaming, sessions/messages CRUD, summarizer, Notion adapter.

    LiteLLM Proxy: local proxy to OpenAI; streaming enabled.

    Store: SQLite (SQLModel/SQLAlchemy).

    Notion: Internal integration via Notion API.

7) Data Model (SQLite; minimal)

    Session

        id (UUID string)

        title (string; auto from first user message ≤80 chars; nullable)

        created_at (timestamp)

    Message

        id (UUID string)

        session_id (FK)

        role (user | assistant)

        content (text)

        created_at (timestamp)

    Summary (optional; can be embedded in Session)

        session_id (PK/FK)

        title (string)

        markdown (text)

        created_at (timestamp)

8) LLM Integration (LiteLLM)

    Proxy: Run locally; forwards to OpenAI; supports streaming.

    Model config: From env (default: gpt-4o-mini).

    Timeouts/Retries: Basic retry once on transient 5xx; fail fast on auth/config errors.

    Token safety: Estimate size; trim chat history for requests; chunk for summarization.

9) Summarization Specification

    Output structure (always present):

        # {Title ≤ 80 chars}

        ## TL;DR (1–2 bullets)

        ## Key Points (bullets)

        ## Action Items (bullets; include “Owner:” and “Due:” only when explicitly present)

        ## Notes (links, code snippets)

    Guardrails:

        Faithful to source; no speculation.

        Use only basic Markdown: #, ##, -, **bold**, `code`.

    Chunking (map-reduce):

        Chunk by ~3–5 message pairs or token heuristic.

        Summarize each chunk → combine into final Markdown.

        Deterministic headings even if sections are empty (allow empty bullets where needed).

10) Notion Integration (Basic Markdown → Blocks)

    Inputs: NOTION_API_KEY, NOTION_PARENT_PAGE_ID.

    Block mapping (v1):

        # → heading_1

        ## → heading_2

        - → bulleted_list_item

        fenced code ``` → code block (language = “markdown”)

        plain line → paragraph

        (Inline bold/code optional; only if trivial, no complex nesting.)

    Behavior:

        Create page under parent with title and children blocks.

        If no summary exists: auto-summarize, then create.

    Failure handling:

        Missing token/parent → 400 with corrective message.

        Notion API error → 502 with brief human-readable message; details in server logs.

11) API Specification (Backend)

Base URL: /api

    GET /healthz

        200: { ok: true }

    POST /sessions

        200: { id: "<uuid>" }

    GET /sessions/{id}

        200: { id, title|null, created_at }

    GET /sessions/{id}/messages

        200: { messages: [ { id, role, content, created_at }, ... ] }

    POST /chat (SSE streaming)

        Body: { session_id, text }

        Response: text/event-stream

            data: <content-chunk>

            …

            event: end → data: done

    POST /sessions/{id}/summarize

        200: { title, markdown }

        Ensures fixed sections; uses chunked map-reduce if long.

    POST /sessions/{id}/notion

        200: { page_id, url }

        If summary missing, auto-summarize before save.

    Common error envelope:

        { error: { code, message, details?, request_id } }

12) Configuration & Security

    Env vars (backend only):

        OPENAI_API_KEY

        MODEL (default: gpt-4o-mini)

        LITELLM_URL (default: http://localhost:4000/v1/chat/completions)

        DATABASE_URL (default: sqlite:///./app.db)

        NOTION_API_KEY

        NOTION_PARENT_PAGE_ID

    CORS: Allow only local frontend origin during dev.

    No keys in client.

    Logging: request_id, model, latency, (token usage if available), Notion page id on success.

13) Performance Targets (Local Baseline)

    First token TTFB: ≤ 2 s typical.

    Streaming cadence: steady updates (< 250 ms gaps typical).

    Summarization: ≤ 8 s for short sessions; ≤ 30 s for long sessions (chunked).

14) Observability & Errors

    Metrics/logs: per-endpoint latency, error rate; LLM/Notion upstream error categorization.

    User-facing messages: concise and actionable; retry option on transient failures.

15) Testing & Acceptance

Unit (backend)

    Sessions/messages CRUD; deterministic ordering.

    Chat SSE emits ≥2 chunks and final end; persists assistant message.

    Summarizer returns all sections for short/long chats.

    Markdown→Notion mapping: H1/H2/bullets/paragraphs/code; malformed lines handled gracefully.

Integration

    End-to-end: send → stream → persist → summarize → save to Notion (URL returned).

    Failure injection: LiteLLM 5xx, Notion 4xx/5xx; verify proper error surfacing and retry ability.

Frontend

    Composer: Enter/Shift+Enter; disabled during stream; Stop works.

    Streaming: tokens append in one bubble; auto-scroll.

    Buttons: Save disabled until summary exists (or triggers auto summarize-then-save).

    Refresh restores session and messages.

Per-phase acceptance (v1)

    P1: Mock chat UX usable.

    P2: Real streaming via SSE; errors handled.

    P3: Persistence verified across refresh.

    P4: Summary returns fixed sections.

    P5: Notion page created; link visible.

16) Milestones

    M0: Scaffolding, healthcheck, env wiring.

    P1: Chat UI (mock).

    P2: Streaming via LiteLLM; persistence of messages.

    P3: Load and render session history on refresh.

    P4: Whole-session summarization.

    P5: Notion export (basic blocks).

17) Sequence (Happy Path)

    User sends message.

    Backend saves user message.

    Backend requests streaming completion from LiteLLM → OpenAI.

    Frontend receives SSE chunks and renders streaming assistant bubble.

    Backend saves final assistant message.

    User clicks Summarize → backend produces fixed-section Markdown.

    User clicks Save to Notion → backend converts Markdown to blocks and creates a page; returns link.

18) Risks & Mitigations

    SSE issues behind certain proxies: Run locally in v1; document proxy requirements.

    Context overflow on long chats: Trim history for chat; chunk map-reduce for summaries.

    Markdown fidelity in Notion: Keep mapping minimal and predictable; avoid tables in v1.