"""
Ingest Lenny's Podcast transcripts into PostgreSQL/pgvector.

Usage:
    python scripts/ingest.py --input ./transcripts --provider ollama

Expects a directory of .txt or .md files, one per episode. Each file should
ideally start with a small metadata header:

    Title: How to find PMF
    Guest: Jane Doe
    Published: 2024-03-01
    ---
    <transcript body>

If no header is found, the filename is used as the title and guest/date are
left null.
"""
import argparse
import asyncio
import re
from pathlib import Path

import tiktoken

from app.database import SessionLocal, init_db
from app.llm_provider import get_provider
from app.models import TranscriptChunk

ENC = tiktoken.get_encoding("cl100k_base")

HEADER_RE = re.compile(
    r"Title:\s*(?P<title>.+)\nGuest:\s*(?P<guest>.*)\nPublished:\s*(?P<date>.*)\n-{3,}\n",
    re.IGNORECASE,
)


def parse_file(path: Path) -> tuple[str, str | None, str | None, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = HEADER_RE.match(text)
    if match:
        return (
            match.group("title").strip(),
            match.group("guest").strip() or None,
            match.group("date").strip() or None,
            text[match.end():],
        )
    return path.stem, None, None, text


def chunk_text(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    tokens = ENC.encode(text)
    chunks = []
    step = target_tokens - overlap_tokens
    for start in range(0, len(tokens), step):
        window = tokens[start : start + target_tokens]
        if not window:
            break
        chunks.append(ENC.decode(window))
        if start + target_tokens >= len(tokens):
            break
    return chunks


async def ingest_directory(input_dir: Path, provider_name: str, target_tokens: int, overlap: int):
    await init_db()
    provider = get_provider(provider_name)
    files = sorted(list(input_dir.glob("*.txt")) + list(input_dir.glob("*.md")))
    if not files:
        print(f"No .txt/.md files found in {input_dir}")
        return

    total_chunks = 0
    async with SessionLocal() as db:
        for path in files:
            title, guest, date, body = parse_file(path)
            pieces = chunk_text(body, target_tokens, overlap)
            print(f"{path.name}: {len(pieces)} chunks (title='{title}', guest='{guest}')")

            for i, piece in enumerate(pieces):
                embedding = await provider.embed(piece)
                db.add(
                    TranscriptChunk(
                        episode_title=title,
                        guest_name=guest,
                        published_at=date,
                        timestamp=f"chunk_{i}",
                        content=piece,
                        embedding=embedding,
                    )
                )
                total_chunks += 1
            await db.commit()

    print(f"Done. Ingested {total_chunks} chunks from {len(files)} episodes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Directory of transcript files")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "anthropic"])
    parser.add_argument("--target-tokens", type=int, default=650)
    parser.add_argument("--overlap-tokens", type=int, default=100)
    args = parser.parse_args()

    asyncio.run(
        ingest_directory(args.input, args.provider, args.target_tokens, args.overlap_tokens)
    )
