"""
Unified LLM client. Swapping providers is a config change (LLM_PROVIDER env
var or `?provider=` request param), never a code change in callers.
"""
from __future__ import annotations

import abc
from collections.abc import AsyncIterator

import httpx
from anthropic import AsyncAnthropic

from app.config import settings


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def chat_stream(self, system: str, messages: list[dict]) -> AsyncIterator[str]:
        """Yield text chunks for a streamed chat completion."""

    @abc.abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""


class OllamaProvider(LLMProvider):
    """Local inference — required for the evaluation demo (offline, zero-cost)."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.chat_model = settings.ollama_chat_model
        self.embed_model = settings.ollama_embed_model

    async def chat_stream(self, system: str, messages: list[dict]) -> AsyncIterator[str]:
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=600) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    import json

                    chunk = json.loads(line)
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=600) as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]


class AnthropicProvider(LLMProvider):
    """Cloud driver — used when local reasoning quality isn't sufficient."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    async def chat_stream(self, system: str, messages: list[dict]) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, text: str) -> list[float]:
        # Anthropic has no native embeddings endpoint; fall back to a local
        # embedding model (Ollama) even when the cloud provider is selected
        # for chat. This keeps a single vector space for retrieval.
        return await OllamaProvider().embed(text)


_PROVIDERS = {"ollama": OllamaProvider, "anthropic": AnthropicProvider}


def get_provider(name: str | None = None) -> LLMProvider:
    """Factory: resolves provider from an explicit name, else config default."""
    key = (name or settings.llm_provider).lower()
    if key not in _PROVIDERS:
        raise ValueError(f"Unknown provider '{key}'. Options: {list(_PROVIDERS)}")
    return _PROVIDERS[key]()
