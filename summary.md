# AI Conversation Intelligence Platform — Build Spec (v1)

## What this is

A local-first web app that takes a WhatsApp chat export (.txt) and generates a unique, data-driven report about that specific conversation — communication stats, personality patterns, relationship dynamics, and "drama" moments — with witty AI-written commentary layered on top of real, computable evidence. No two reports should read the same, because the set of patterns detected differs per chat, not just the wording.

Core principle: **analytics first, AI second.** Almost everything must be computed deterministically by code. The LLM's only job is to narrate the specific patterns that were actually detected in this chat, using real numbers and real quoted messages. The LLM never invents facts and never sees the full raw transcript — only structured stats and a small set of algorithmically-selected representative messages.

---

## Tech stack

- Backend: Python, FastAPI, running locally only (localhost, no public exposure in v1)
- Database: SQLite for v1, schema written to be Postgres-compatible (no SQLite-only features) so it can migrate to Supabase/hosted Postgres later without a rewrite
- Frontend: React + Vite + TypeScript, Tailwind for styling
- Sentiment analysis: VADER (lightweight, no API cost) or a small local transformer if VADER proves too crude
- LLM calls: free-tier API keys (e.g. Gemini free tier, or other generous free-tier LLM APIs) — used ONLY for caption/commentary generation, never for analytics or fact-finding
- PDF export: deferred to Phase 3, will use Playwright/Puppeteer to render the web report to PDF once the UI is stable

---

## Privacy rules (non-negotiable, hard-coded into architecture)

1. Raw chat text never leaves the local machine except as algorithmically-selected short excerpts sent to the LLM for narration.
2. The LLM receives: aggregated stats (counts, ratios, timestamps, scores) + a small number of specific messages chosen by the analytics engine (e.g. highest-engagement message, clearest example of a detected pattern). It never receives the full transcript.
3. After parsing, the raw uploaded chat file is deleted from disk by default; only the structured/parsed data (messages broken into sender/timestamp/text in the local DB) is retained, and even that should have a clear delete option in the UI.
4. No analytics, pattern detection, or relationship scoring may run via an external API call — only local code (Python). The only network calls in v1 are to the LLM API for narration text.

---

## Pipeline

```
WhatsApp .txt export
  → Parser (regex-based, handles WhatsApp's line format, multi-line messages, media/system messages)
  → Structured messages table (sender, timestamp, text, message_type) in SQLite
  → Analytics Engine (pure Python, no AI, unit-tested)
      - per-person stats
      - per-pair relationship stats
      - pattern detection (rule-based trigger library)
      - representative message selection
  → Stats + selected excerpts packaged as JSON
  → LLM call (free-tier API) — generates captions/commentary ONLY for patterns that actually triggered
  → React frontend renders report from structured JSON + AI captions
```

---

## Database schema (SQLite now, Postgres-compatible)

**chats**
- id (pk)
- name / label
- uploaded_at
- raw_file_deleted (bool)

**participants**
- id (pk)
- chat_id (fk)
- display_name
- normalized_name (handles inconsistent contact name formats)

**messages**
- id (pk)
- chat_id (fk)
- sender_id (fk → participants)
- timestamp
- text
- message_type (text / media / system / deleted)

**pattern_results**
- id (pk)
- chat_id (fk)
- pattern_key (e.g. "ghosting_period", "double_texting", "late_night_spike")
- triggered (bool)
- evidence_json (the specific stats/messages that justify this trigger)
- score (optional severity/confidence number)

**relationship_scores**
- id (pk)
- chat_id (fk)
- participant_a_id, participant_b_id
- avg_reply_time_a_to_b, avg_reply_time_b_to_a
- initiation_ratio
- closeness_score

Keep all of this in plain SQL tables, avoid SQLite-only pragmas/JSON1-specific tricks beyond basic JSON storage, so a future `pg_dump`-style migration to Supabase is mechanical.

---

## Analytics engine — what must be computed with NO AI involved

**Per-person stats**
- total messages sent
- average response time
- active hours/days (for heatmap)
- longest streak of consecutive days messaging
- word/emoji frequency
- conversation starter vs ender ratio
- message length trend over time

**Per-pair relationship stats**
- reply-time matrix (A→B vs B→A average response time)
- message-initiation ratio (who starts conversations more)
- closeness score (composite of reply speed symmetry + initiation balance + message volume)

**Pattern detection library (rule-based, threshold-driven — v1 target ~15-20 patterns, expand later)**
Each pattern is a function: input = parsed messages, output = triggered (bool) + evidence. Examples to start with:
- Ghosting period (gap between messages > N days)
- One-sided conversation (initiation ratio heavily skewed)
- Double-texting habit (sends 2+ messages in a row with no reply, repeatedly)
- Late-night spike (disproportionate share of messages between e.g. 12am-4am)
- Reply-time asymmetry (one person consistently replies much faster/slower)
- Sentiment dip + recovery (possible argument-then-makeup, via VADER score drop then rise)
- Sudden topic/tone shift (large jump in message length or sentiment between adjacent days)
- Conversation killer (messages that reliably end the thread for >X hours)
- Streak holder (longest daily messaging streak)
- Emoji/reaction signature (heavy or unusual use of a specific emoji)

Rule-based and threshold-driven on purpose — every conclusion must be traceable to a specific, explainable threshold. No ML clustering in v1; that can be explored later once the rule-based version is validated, but it shouldn't replace explainability.

**Representative message selection**
For each triggered pattern, the engine picks 1-3 actual messages that best illustrate it (e.g. the message right before a long gap, the message with the most dramatic sentiment drop). These are the only raw text snippets that get sent to the LLM.

---

## What gets sent to the LLM (and the prompt shape)

Input to the LLM per chat: a JSON payload containing only the triggered patterns, their evidence stats, and the small set of selected message excerpts (no full transcript). The system prompt should establish: clever/witty/dry/observant tone, roast without cruelty, praise without sounding fake, and a hard rule to only narrate what's in the provided evidence — never invent details, never speculate beyond the data. Ask it to explicitly reference the numbers/excerpts it was given so every claim is traceable.

Output: short caption/blurb per pattern/award (a few sentences each), not a single giant essay — these map directly to report cards in the UI.

---

## Report structure (v1, solo-chat / two-person focus — skip multi-person group dynamics for now)

1. Cover page (chat name, date range, message count)
2. Quick stats (total messages, most active person, busiest day)
3. Individual stat cards (per person: response time, streaks, style)
4. Relationship score card (closeness, initiation balance, reply symmetry)
5. Activity heatmap (calendar-style, like GitHub contributions — purely computed, no AI)
6. Triggered pattern/award cards (only the ones that actually fired for this chat, each with AI caption + evidence)
7. Shareable summary card (single image-exportable card combining the top 2-3 highlights)

Explicitly cut for v1: group chat support, multi-person relationship maps, semantic "ask your chat" search, PDF export, public share pages. These are Phase 2/3.

---

## Build order for Antigravity

1. WhatsApp .txt parser → SQLite (messages, participants tables). Validate against a real exported chat.
2. Per-person analytics functions (pure Python, unit tests against known sample data).
3. Per-pair relationship scoring functions.
4. Pattern detection library (start with 5-6 patterns, expand once the pipeline works end to end).
5. JSON packaging layer that turns analytics output into the exact payload structure sent to the LLM.
6. LLM integration (free-tier API key) for caption generation — isolated module, easy to swap providers later.
7. FastAPI endpoints: upload chat, trigger analysis, fetch report JSON.
8. React frontend: upload flow + report page rendering cards from the JSON, heatmap component, award cards.
9. Raw file deletion after parsing (privacy requirement, build this in from the start, not bolted on later).

---

## Explicit non-goals for v1

- No hosting/deployment (local only)
- No multi-person group chat analysis
- No PDF export
- No semantic search / "ask your chat"
- No ML-based pattern discovery (rule-based only)
- No user accounts/auth (single local user)