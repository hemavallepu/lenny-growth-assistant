# Architecture Spec — The Lenny Growth Assistant

## System Overview
```
┌─────────────┐      HTTP/stream       ┌──────────────┐      SQL/vector      ┌─────────────┐
│  Frontend    │ ─────────────────────▶│   Backend    │ ────────────────────▶│  PostgreSQL │
│  (static JS) │◀───────────────────── │  (FastAPI)   │◀──────────────────── │  + pgvector │
└─────────────┘   streamed text/plain   └──────┬───────┘                     └─────────────┘
                                                │
                                    ┌───────────┴────────────┐
                                    ▼                         ▼
                            ┌──────────────┐          ┌──────────────┐
                            │  Ollama       │          │  Anthropic    │
                            │  (local)      │          │  (cloud)      │
                            └──────────────┘          └──────────────┘
```

## Data Contracts

### `transcript_chunks`
| column | type | notes |
|---|---|---|
| id | UUID | PK |
| episode_title | text | from ingestion header |
| guest_name | text | nullable |
| published_at | text | nullable |
| timestamp | text | chunk index within episode |
| content | text | 500–800 tokens, 100-token overlap |
| embedding | vector(768) | cosine similarity via `ivfflat` index |

### `chat_sessions` / `messages`
Standard session → many messages. `messages.citations` is JSONB reserved for
structured citation metadata (episode/guest/score) if the frontend needs it
beyond inline text citations.

## Model Routing
`app/llm_provider.py` defines an abstract `LLMProvider` with `chat_stream()`
and `embed()`. Two concrete drivers (`OllamaProvider`, `AnthropicProvider`)
implement it. Selection order:
1. Explicit `provider` field on the `/api/chat` request (frontend toggle)
2. `LLM_PROVIDER` env var (deployment default)

Embeddings always route through Ollama's `nomic-embed-text` regardless of
which provider is answering the chat — this keeps one consistent vector
space in `transcript_chunks`, since Anthropic has no embeddings endpoint.

## Retrieval Flow
1. Embed incoming query (768-dim, same space as ingested chunks).
2. Cosine similarity search in pgvector, top `K=5`.
3. If best score < `SIMILARITY_THRESHOLD` (0.35) → return the fixed
   "insufficient information" refusal, skip the LLM call entirely.
4. Else build `<context>` block with excerpt + episode/guest/timestamp tags,
   inject into the grounded system prompt, stream the model's response.

## Security
- Artifact HTML is rendered in an `<iframe sandbox="allow-scripts">` —
  **no** `allow-same-origin`, which blocks access to the parent page's
  cookies/localStorage.
- All artifact content (Markdown and HTML) passes through DOMPurify before
  insertion into the DOM.
- CORS restricted to the configured frontend origin(s) only.

## Deployment
Four Docker Compose services: `db` (Postgres 16 + pgvector), `ollama`
(pulls `llama3.1:8b` + `nomic-embed-text` on boot), `backend` (FastAPI),
`frontend` (static Nginx). Single command: `docker compose up`.
