# Docker Compose & Dockerfile Scaffolding

## Task
Set up a single-command deployable environment for the Lenny Growth
Assistant using Docker Compose, covering the backend (FastAPI), frontend,
and PostgreSQL with the pgvector extension.

## What I asked Claude
"Help me write a docker-compose.yml for this project. I need a Postgres
service with the pgvector extension, a FastAPI backend service, and a
frontend service, all wired together so I can run the whole thing with
one command."

## What Claude produced
A docker-compose.yml with three services:
- `db`: using the `pgvector/pgvector:pg16` image, with environment
  variables for the Postgres user/password/database name, a volume for
  persistent storage, and a healthcheck using `pg_isready`.
- `backend`: built from a local Dockerfile, with a `DATABASE_URL`
  pointing at the `db` service by container name, and a `depends_on`
  condition waiting for the database healthcheck to pass before starting.
- `frontend`: built from its own Dockerfile, exposing port 3000, with an
  environment variable pointing at the backend's API URL.

Claude also generated a starter `backend/Dockerfile` using a
`python:3.11-slim` base image, and a `frontend/Dockerfile` for serving
the static HTML/CSS/JS files.

## Correction / iteration
The backend container initially couldn't reach Ollama, which was running
on the Windows host machine rather than inside a container. The backend
was trying to call `http://localhost:11434`, which inside a container
refers to the container itself, not the host machine. I asked Claude to
fix this, and it added `extra_hosts: - "host.docker.internal:host-gateway"`
to the backend service and updated the Ollama base URL environment
variable to `http://host.docker.internal:11434` instead of `localhost`.

There was also a port conflict on first run — port 5432 was already in
use by a local Postgres installation on my machine. I changed the host
port mapping to `5433:5432` so the container's internal port stayed the
same but avoided colliding with the existing local instance.

## Outcome
After both fixes, `docker compose up --build` successfully started all
three services, with the backend able to reach both PostgreSQL and the
host-installed Ollama instance.
