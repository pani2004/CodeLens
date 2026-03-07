"""Embedding service — generate vector embeddings using Gemini text-embedding."""

import asyncio
import logging
from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("codelens.embeddings")

# ── Singleton embedding model ────────────────────────────
_embeddings_model: Optional[GoogleGenerativeAIEmbeddings] = None


def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Lazy-init the Gemini embedding model."""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )
    return _embeddings_model


async def generate_embedding(text: str) -> list[float]:
    """Generate a single embedding vector (768-dim)."""
    model = get_embeddings_model()
    try:
        embedding = await asyncio.to_thread(model.embed_query, text)
        return embedding
    except Exception as e:
        logger.error("Embedding error: %s", e)
        raise


async def batch_generate_embeddings(
    texts: list[str],
    batch_size: int = 25,
) -> list[list[float]]:
    """
    Generate embeddings in batches with rate-limit handling.
    """
    model = get_embeddings_model()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                embeddings = await asyncio.to_thread(model.embed_documents, batch)
                all_embeddings.extend(embeddings)
                logger.info("Embedded batch %d-%d / %d", i, i + len(batch), len(texts))
                break
            except Exception as e:
                error_msg = str(e)
                retries += 1
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    import re
                    retry_match = re.search(r'retry in (\d+\.?\d*)s', error_msg)
                    wait = float(retry_match.group(1)) if retry_match else 60
                    logger.warning("Rate limit hit (attempt %d/%d). Waiting %ds before retry...", retries, max_retries, wait)
                else:
                    wait = 2 ** retries
                    logger.warning("Embedding batch failed (attempt %d/%d): %s — retrying in %ds", retries, max_retries, e, wait)
                
                await asyncio.sleep(wait)
                if retries == max_retries:
                    raise

        if i + batch_size < len(texts):
            delay = 18  
            logger.info("Waiting %ds before next batch to respect rate limits...", delay)
            await asyncio.sleep(delay)

    return all_embeddings
