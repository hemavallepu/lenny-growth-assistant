# Docker & Ollama Setup — Debugging Session

## Task
Get the full stack (backend, frontend, PostgreSQL/pgvector, Ollama) running
locally via Docker Compose, and confirm which local LLM model was actually
loaded and being used for testing.

## What I asked Claude
Set up Docker Compose for the project, then later asked how to verify which
Ollama chat model was actually configured and running, since I wasn't sure
if it was `llama3.1:8b` or one of the smaller models I'd pulled earlier.

## What happened / errors encountered
1. Ran `ollama list` and `ollama ps` directly in PowerShell — failed with
   `CommandNotFoundException`, because Ollama runs inside the Docker
   container, not installed on the Windows host directly.
2. Ran `docker compose exec ollama ollama list` — failed with
   `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.
   Root cause: Docker Desktop wasn't running yet.
3. Started Docker Desktop, waited for it to fully initialize, then re-ran
   the same command.
4. `docker compose exec ollama ollama list` succeeded, showing four pulled
   models: `llama3.1:8b` (4.9 GB), `nomic-embed-text:latest` (274 MB),
   and two older leftovers (`llama3.2:3b`, `llama3.2:1b`) from earlier
   testing that are no longer used by the app.
5. Also tried `docker compose exec backend curl ...` to hit the health
   endpoint directly — this failed separately with
   `exec: "curl": executable file not found in $PATH`, since the backend
   image doesn't have `curl` installed. Not fixed — not needed, since the
   model was already confirmed via the `ollama` container directly.

## Correction / what I learned
- Commands need to be run *inside* the correct container via
  `docker compose exec <service> <command>`, not on the Windows host —
  the host has no `ollama` binary at all.
- Docker Desktop must be fully started before any `docker compose`
  command will work; the npipe connection error is a strong signal to
  check that first, not a Compose file problem.
- Confirmed active chat model: **llama3.1:8b**. Confirmed embedding
  model: **nomic-embed-text:latest**. The two smaller `llama3.2` models
  present in the image are unused leftovers from earlier local testing.

## Outcome
Verified the correct chat model in use for the demo/testing without
needing to modify any code — confirmed directly via the running
container's `ollama list` output, cross-checked against the model name
documented in the README.
