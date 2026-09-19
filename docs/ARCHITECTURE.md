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

### `transcript\_chunks`

|column|type|notes|
|-|-|-|
|id|UUID|PK|
|episode\_title|text|from ingestion header|
|guest\_name|text|nullable|
|published\_at|text|nullable|
|timestamp|text|chunk index within episode|
|content|text|500–800 tokens, 100-token overlap|
|embedding|vector(768)|cosine similarity via `ivfflat` index|

### `chat\_sessions` / `messages`

Standard session → many messages. `messages.citations` is JSONB reserved for
structured citation metadata (episode/guest/score) if the frontend needs it
beyond inline text citations.

## Model Routing

`app/llm\_provider.py` defines an abstract `LLMProvider` with `chat\_stream()`
and `embed()`. Two concrete drivers (`OllamaProvider`, `AnthropicProvider`)
implement it. Selection order:

1. Explicit `provider` field on the `/api/chat` request (frontend toggle)
2. `LLM\_PROVIDER` env var (deployment default)

Embeddings always route through Ollama's `nomic-embed-text` regardless of
which provider is answering the chat — this keeps one consistent vector
space in `transcript\_chunks`, since Anthropic has no embeddings endpoint.

## Agent Framework Trade-off

the Claude Agent SDK or Pi Coding Agent. This implementation uses the

plain Anthropic Python SDK (`anthropic==0.34.2`) directly instead.



**Reasoning:** The Claude Agent SDK wraps the Claude Code CLI as a

subprocess, requiring a Node.js runtime and the `@anthropic-ai/claude-code`

CLI installed alongside the Python backend — both in local development

and inside the Docker image. Given this project's core requirement is a

lightweight, single-command-deployable RAG service (see Deployment),

adding a CLI-subprocess dependency increases deployment surface area

(extra runtime, extra container layer, subprocess lifecycle management)

without a corresponding benefit for this use case, since the assistant's

tool needs — retrieval and the Ship 30/30 skill — are already served

well by direct function calls inside `retrieval.py` and `ship30.py`.



**Trade-off accepted:** A direct API client is simpler to deploy and

debug, but forgoes the Agent SDK's built-in tool-orchestration and

session primitives. If this were extended into a multi-step agentic

workflow (e.g. autonomous multi-turn research across episodes), the

Agent SDK would become the stronger choice and this decision should be

revisited.

## Retrieval Flow

1. Embed incoming query (768-dim, same space as ingested chunks).
2. Cosine similarity search in pgvector, top `K=5`.
3. If best score < `SIMILARITY\_THRESHOLD` (0.35) → return the fixed
"insufficient information" refusal, skip the LLM call entirely.
4. Else build `<context>` block with excerpt + episode/guest/timestamp tags,
inject into the grounded system prompt, stream the model's response.

## Security

* Artifact HTML is rendered in an `<iframe sandbox="allow-scripts">` —
**no** `allow-same-origin`, which blocks access to the parent page's
cookies/localStorage.
* All artifact content (Markdown and HTML) passes through DOMPurify before
insertion into the DOM.
* CORS restricted to the configured frontend origin(s) only.

## Deployment

Four Docker Compose services: `db` (Postgres 16 + pgvector), `ollama`
(pulls `llama3.1:8b` + `nomic-embed-text` on boot), `backend` (FastAPI),
`frontend` (static Nginx). Single command: `docker compose up`.

