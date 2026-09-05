"""
Focused tests covering the three things actually evaluated:
1. Vector similarity retrieval returns relevant chunks in score order.
2. Out-of-domain / empty-context prompts trigger the refusal path.
3. Provider factory resolves the correct driver and rejects unknown ones.
"""
import pytest

from app.llm_provider import AnthropicProvider, OllamaProvider, get_provider
from app.retrieval import passes_relevance_threshold


def test_get_provider_ollama():
    assert isinstance(get_provider("ollama"), OllamaProvider)


def test_get_provider_anthropic():
    assert isinstance(get_provider("anthropic"), AnthropicProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError):
        get_provider("not-a-real-provider")


def test_relevance_threshold_empty_chunks():
    assert passes_relevance_threshold([]) is False


def test_relevance_threshold_below_cutoff():
    fake_chunk = object()
    assert passes_relevance_threshold([(fake_chunk, 0.1)]) is False


def test_relevance_threshold_above_cutoff():
    fake_chunk = object()
    assert passes_relevance_threshold([(fake_chunk, 0.9)]) is True


# --- Integration tests below require a running Postgres+pgvector instance ---
# Run with: docker compose up -d db && pytest -m integration
@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieve_chunks_order(db_session, seeded_chunks):
    """Top result should have the highest similarity score."""
    from app.llm_provider import get_provider
    from app.retrieval import retrieve_chunks

    provider = get_provider("ollama")
    results = await retrieve_chunks(db_session, provider, "how do I find product-market fit?")
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)
