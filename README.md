# The Lenny Growth Assistant

Grounded RAG assistant over Lenny's Podcast transcripts, with a Ship 30/30
essay generator and a sandboxed artifact viewer. See `docs/PRD.md`,
`docs/ARCHITECTURE.md`, `docs/DESIGN.md` for the discovery documents.

## Quick Start (Windows 11 + Docker Desktop)

1. Install Docker Desktop (WSL2 backend) — see install guide if not done yet.
2. Open **PowerShell** in this project folder.
3. Copy the env template:
   ```powershell
   copy backend\.env.example backend\.env
   ```
   (Optional) Paste an Anthropic API key into `backend\.env` if you want to
   demo the cloud provider too — not required for the core local demo.
4. Start everything:
   ```powershell
   docker compose up --build
   ```
   First run will take a few minutes — it pulls the Ollama models
   (`llama3.1:8b`, `nomic-embed-text`), which are several GB.
5. Once you see the backend log `startup complete — provider=ollama`,
   open the frontend: **http://localhost:3000**
6. Backend health check: **http://localhost:8000/api/health**

## Ingest transcripts

Put a handful of `.txt`/`.md` transcript files in `./transcripts` (5-10
episodes is enough for a demo), each optionally starting with:

```
Title: Episode title
Guest: Guest name
Published: 2024-03-01
---
<transcript text>
```

Then, with the `db` service running:

```powershell
docker compose exec backend python scripts/ingest.py --input /app/../transcripts
```

(Or run the ingestion script on your host with `pip install -r backend/requirements.txt`
and `DATABASE_URL` pointed at `localhost:5432` if you'd rather not exec into
the container.)

## Running tests

```powershell
docker compose exec backend pytest
```

## Known gaps (documented, not hidden)

- Frontend is a single-file vanilla-JS app, not the full Next.js app listed
  in the reference doc — trimmed to fit the deadline; state/streaming logic
  is equivalent.
- Mobile/tablet responsive layout for the artifact pane is not yet built.
- Structured JSON logging is basic (Python `logging`, not a structured
  logger like `structlog`) — sufficient for the demo, flagged for follow-up.

## Demo video checklist (record 2-3 min)

1. `docker compose up` from a clean state — show it coming up.
2. Ask a grounded question → show the streamed answer + citations.
3. Ask something off-topic → show the "insufficient information" refusal.
4. Switch to Ship 30/30 mode → show the essay render in the artifact pane.
5. Toggle the provider badge (ollama → anthropic) → ask again, note the
   trade-off in response quality/latency out loud.
