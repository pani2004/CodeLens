"""Embedding generation Celery tasks."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.models import CodeChunk
from app.services.embedding_service import batch_generate_embeddings

logger = logging.getLogger("codelens.tasks.embedding")


@celery_app.task(name="generate_embeddings", max_retries=2, default_retry_delay=60)
def generate_embeddings_task(repo_id: str):
    """Celery task wrapper for embedding generation."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run_embeddings(repo_id))
    finally:
        loop.close()


async def _run_embeddings(repo_id: str):
    """Standalone async embedding runner (for Celery)."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        await _generate_embeddings_for_repo(repo_id, db)

    await engine.dispose()


async def _generate_embeddings_for_repo(repo_id: str, db: AsyncSession):
    """
    Generate embeddings for all code chunks in a repository.
    Called from both the Celery task and the analysis pipeline.
    """
    # Fetch chunks without embeddings
    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .where(CodeChunk.embedding.is_(None))
    )
    chunks = result.scalars().all()

    if not chunks:
        logger.info("[%s] No chunks need embedding", repo_id)
        return

    logger.info("[%s] Generating embeddings for %d chunks", repo_id, len(chunks))

    # Prepare texts for embedding
    texts = []
    for chunk in chunks:
        # Create rich text representation for better embeddings
        text = f"File: {chunk.file_path}\nType: {chunk.chunk_type}\nLanguage: {chunk.language}\n\n{chunk.content}"
        texts.append(text[:8000])  # Gemini embedding limit

    # Generate embeddings in batches
    embeddings = await batch_generate_embeddings(texts, batch_size=25)

    # Update chunks with embeddings
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    await db.commit()
    logger.info("[%s] Embeddings generated for %d chunks", repo_id, len(chunks))
