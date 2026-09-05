from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm_provider import LLMProvider
from app.models import TranscriptChunk

GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an expert research aide for \
product managers and growth leaders. Answer ONLY using the transcript excerpts provided \
in <context>. Every factual claim must be followed by an inline citation in the form \
[Episode: <title>, Guest: <guest>]. If the excerpts do not contain enough information to \
answer confidently, respond exactly: "I do not have sufficient information in Lenny's \
podcast archive to answer this." Do not use outside knowledge."""


async def retrieve_chunks(
    db: AsyncSession, provider: LLMProvider, query: str, k: int | None = None
) -> list[tuple[TranscriptChunk, float]]:
    """Embed the query and return the top-k chunks by cosine similarity,
    each paired with its similarity score (1 - cosine_distance)."""
    query_embedding = await provider.embed(query)
    k = k or settings.top_k

    distance = TranscriptChunk.embedding.cosine_distance(query_embedding)
    stmt = select(TranscriptChunk, distance.label("distance")).order_by(distance).limit(k)
    result = await db.execute(stmt)
    rows = result.all()
    return [(chunk, 1 - dist) for chunk, dist in rows]


def build_grounded_context(scored_chunks: list[tuple[TranscriptChunk, float]]) -> str:
    if not scored_chunks:
        return ""
    parts = []
    for chunk, score in scored_chunks:
        parts.append(
            f"<excerpt episode=\"{chunk.episode_title}\" guest=\"{chunk.guest_name}\" "
            f"timestamp=\"{chunk.timestamp}\" score=\"{score:.2f}\">\n{chunk.content}\n</excerpt>"
        )
    return "<context>\n" + "\n\n".join(parts) + "\n</context>"


def passes_relevance_threshold(scored_chunks: list[tuple[TranscriptChunk, float]]) -> bool:
    if not scored_chunks:
        return False
    return scored_chunks[0][1] >= settings.similarity_threshold
