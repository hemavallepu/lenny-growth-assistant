# PRD — The Lenny Growth Assistant

## Persona

**Growth PM / product leader** who wants actionable, source-backed tactics from
Lenny's Podcast without listening to 200+ hours of audio. They ask a question,
get a grounded answer with citations, and can optionally turn it into a
shareable essay for their team.

## Problem

Podcast knowledge is trapped in unstructured audio/transcripts. Search is
manual (Ctrl+F across transcript files) and doesn't synthesize across
episodes. Existing summaries are generic, not grounded in specific guest
insights, and not attributable.

## Success Metrics

|Metric|Target|
|-|-|
|Retrieval Citation Accuracy|≥ 90% (cited episode/guest actually supports the claim)|
|Local Inference Latency|< 4s to first token (Ollama, 7B/8B model)|
|Artifact Render Safety|0 XSS vulnerabilities (sandboxed iframe, no `allow-same-origin`)|
|Grounded Refusal Rate|100% of out-of-domain questions correctly refused|

## Core Features

1. **Grounded Q\&A** — answers strictly from transcript chunks, inline citations,
explicit "insufficient information" fallback.
2. **Ship 30 for 30 Content Engine** — reframes a grounded answer as a
\~1,250-word, high-retention essay following Ship 30/30 formatting rules.
3. **Artifact Viewer** — Claude-Artifacts-style side panel rendering Markdown
or sandboxed HTML/CSS.
4. **Dual Model Layer** — Ollama (local, required for demo) and
Anthropic/OpenAI (cloud), switchable via env var or request header —
zero code changes.

## Trade-offs

* **Local 8B model reasoning limits vs. cloud autonomy**: local models are
faster to demo and free, but weaker at nuanced synthesis across many
chunks. Cloud provider is the fallback for higher-quality output; the
local path is what's required for the evaluation demo.
* **pgvector vs. dedicated vector DB**: chose pgvector to keep the stack to
one database (relational + vector), trading some ANN performance at scale
for operational simplicity — acceptable given the transcript corpus size.
* **IVFFlat vs. HNSW index**: IVFFlat chosen for faster build time on a
small corpus; HNSW would be preferable at scale (100k+ chunks).
* **Scope cut for the deadline**: full Next.js app and exhaustive test suite
were trimmed in favor of a working vanilla-JS frontend and a focused test
set covering retrieval, refusal, and provider switching — the three things
actually graded.
* **Model size vs. speed:** started with llama3.1:8b (CPU inference exceeded

&#x20;  5 minutes per response — unusable for a live demo). Tested llama3.2:1b

&#x20;  (fast, \~1min, but incoherent answers). Settled on llama3.2:3b as the

&#x20;  right balance — coherent, grounded answers in 6-50s on CPU-only hardware.

* **Similarity threshold tuning:** nomic-embed-text cosine scores for true

&#x20;  matches cluster around 0.4-0.6, not near 1.0. Initial threshold of 0.35

&#x20;  caused false refusals on genuinely relevant questions. Tuned down to

&#x20;  0.15 empirically by logging real query scores rather than guessing.

