import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, init_db
from app.llm_provider import get_provider
from app.models import ChatSession, Message
from app.retrieval import (
    GROUNDED_SYSTEM_PROMPT,
    build_grounded_context,
    passes_relevance_threshold,
    retrieve_chunks,
)
from app.ship30 import SHIP30_SYSTEM_PROMPT, build_ship30_user_prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("lenny")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    log.info("startup complete — provider=%s", settings.llm_provider)
    yield


app = FastAPI(title="Lenny Growth Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- schemas ----------
class SessionCreate(BaseModel):
    title: str = "New chat"
    provider: str = settings.llm_provider


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str
    provider: str | None = None  # per-request override, e.g. from a UI toggle
    mode: str = "qa"  # "qa" | "ship30"


# ---------- routes ----------
@app.post("/api/sessions")
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(title=body.title, provider=body.provider)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": session.id, "title": session.title, "provider": session.provider}


@app.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    return result.scalars().all()


@app.post("/api/chat")
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Streams a grounded (or Ship 30/30) response. Retrieval always runs
    against the transcript archive; `mode` decides how the answer is framed."""
    provider = get_provider(body.provider)

    db.add(Message(session_id=body.session_id, role="user", content=body.message))
    await db.commit()

    scored_chunks = await retrieve_chunks(db, provider, body.message)
    context = build_grounded_context(scored_chunks)

    top_scores = [round(score, 3) for _, score in scored_chunks[:5]]
    log.info("query=%r top_scores=%s threshold=%s", body.message, top_scores, settings.similarity_threshold)

    if not passes_relevance_threshold(scored_chunks):
        async def no_context_stream():
            text = (
                "I do not have sufficient information in Lenny's podcast archive "
                "to answer this."
            )
            yield text
            db.add(Message(session_id=body.session_id, role="assistant", content=text))
            await db.commit()

        return StreamingResponse(no_context_stream(), media_type="text/plain")

    if body.mode == "ship30":
        system = SHIP30_SYSTEM_PROMPT
        user_content = build_ship30_user_prompt(body.message, "", context)
    else:
        system = GROUNDED_SYSTEM_PROMPT
        user_content = f"{context}\n\nQuestion: {body.message}"

    async def event_stream():
        full = []
        try:
            async for piece in provider.chat_stream(system, [{"role": "user", "content": user_content}]):
                full.append(piece)
                yield piece
        except httpx.HTTPError as exc:
            log.exception("provider error")
            yield f"\n[error: provider unavailable — {exc}]"
        finally:
            answer = "".join(full)
            if answer:
                db.add(Message(session_id=body.session_id, role="assistant", content=answer))
                await db.commit()

    return StreamingResponse(event_stream(), media_type="text/plain")


@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    checks = {"database": "ok", "ollama": "unknown", "vector_index": "ok"}
    try:
        await db.execute(select(1))
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            checks["ollama"] = "ok" if r.status_code == 200 else f"error: {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        checks["ollama"] = f"unreachable: {exc}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "active_provider": settings.llm_provider}