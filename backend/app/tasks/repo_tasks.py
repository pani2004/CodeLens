"""Repository analysis Celery tasks — clone, parse, chunk, store."""

import os
import shutil
import tempfile
import logging
import asyncio
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.models import Repository, CodeChunk, User, ChatHistory
from app.services.github_service import download_repo_tarball, get_repo_info
from app.services.parser_service import extract_tarball, get_repo_files, chunk_file, build_file_tree
from app.utils.validators import parse_github_url
from app.utils.crypto import decrypt_token
from app.tasks.embedding_tasks import _generate_embeddings_for_repo

settings = get_settings()
logger = logging.getLogger("codelens.tasks.repo")


def _run_async(coro):
    """Helper to run async code in sync Celery context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="analyze_repo",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def analyze_repo_task(self, repo_id: str, user_id: str):
    """
    Main analysis pipeline:
    1. Clone repository (download tarball)
    2. Parse files into chunks
    3. Save chunks to DB
    4. Generate embeddings
    5. Build dependency graph
    6. Generate summary
    """
    try:
        _run_async(_analyze_repo_async(self, repo_id, user_id))
    except Exception as exc:
        logger.error("analyze_repo_task failed: %s", exc)
        # Update status to failed
        _run_async(_update_status(repo_id, "failed", 0, str(exc)))
        raise self.retry(exc=exc)


async def _analyze_repo_async(task, repo_id: str, user_id: str):
    """Async implementation of the analysis pipeline."""
    # Create a fresh DB session for this task
    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Fetch repo record
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if not repo:
            logger.error("Repository %s not found", repo_id)
            return

        # Update status
        repo.status = "processing"
        repo.processing_progress = 5.0
        repo.error_message = "Initializing analysis..."
        await db.commit()
        logger.info("[%s] ✓ Analysis started", repo_id)

        # Get user's GitHub token
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        github_token = None
        if user and user.access_token_encrypted:
            try:
                github_token = decrypt_token(user.access_token_encrypted)
            except Exception:
                pass

        owner, repo_name = parse_github_url(repo.github_url)

        # ── Step 1: Clone (download tarball) ─────────────
        logger.info("[%s]   Cloning repository from GitHub...", repo_id)
        repo.processing_progress = 10.0
        repo.error_message = "Cloning repository from GitHub..."
        await db.commit()

        try:
            repo_info = await get_repo_info(owner, repo_name, github_token)
            tarball = await download_repo_tarball(
                owner, repo_name, repo_info.get("default_branch", "main"), github_token
            )
        except Exception as e:
            repo.status = "failed"
            repo.error_message = f"Failed to download repository: {e}"
            await db.commit()
            return

        # Extract to temp directory
        tmp_dir = tempfile.mkdtemp(prefix="codelens_")
        try:
            logger.info("[%s]  Extracting repository archive...", repo_id)
            repo_path = extract_tarball(tarball, tmp_dir)

            repo.processing_progress = 25.0
            repo.error_message = "Extracting files..."
            await db.commit()

            # ── Step 2: Parse files ──────────────────────
            logger.info("[%s]  Scanning repository structure...", repo_id)
            files = get_repo_files(repo_path)
            total_files = len(files)
            logger.info("[%s] ✓ Found %d files to analyze", repo_id, total_files)

            repo.processing_progress = 30.0
            repo.error_message = f"Scanning files... ({total_files} files found)"
            await db.commit()

            # ── Step 3: Chunk files ──────────────────────
            logger.info("[%s]  Parsing and chunking code files...", repo_id)
            repo.error_message = "Parsing code structure..."
            await db.commit()

            # Delete existing chunks
            await db.execute(delete(CodeChunk).where(CodeChunk.repo_id == repo_id))

            all_chunks = []
            for i, file_info in enumerate(files):
                try:
                    with open(file_info["full_path"], "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    chunks = chunk_file(content, file_info["path"], file_info["language"])
                    all_chunks.extend(chunks)

                except Exception as e:
                    logger.warning("[%s] Failed to process %s: %s", repo_id, file_info["path"], e)

                # Update progress (30-60%)
                if total_files > 0:
                    progress = 30 + (i / total_files) * 30
                    repo.processing_progress = progress
                    if i % 50 == 0:
                        await db.commit()

            repo.processing_progress = 60.0
            repo.error_message = f"Code parsing complete ({len(all_chunks)} chunks)"
            await db.commit()

            # ── Step 4: Save chunks to DB ────────────────
            logger.info("[%s]  Saving %d code chunks to database...", repo_id, len(all_chunks))
            repo.error_message = "Saving code chunks to database..."
            await db.commit()

            for chunk_data in all_chunks:
                chunk = CodeChunk(
                    repo_id=repo_id,
                    file_path=chunk_data["file_path"],
                    chunk_type=chunk_data["chunk_type"],
                    content=chunk_data["content"],
                    language=chunk_data.get("language", "text"),
                    start_line=chunk_data["start_line"],
                    end_line=chunk_data["end_line"],
                    metadata_jsonb=chunk_data.get("metadata", {}),
                )
                db.add(chunk)

            await db.commit()
            repo.processing_progress = 70.0
            repo.error_message = "Code chunks saved successfully"
            await db.commit()

            # ── Step 5: Generate embeddings ──────────────
            logger.info("[%s]  Generating AI embeddings for semantic search...", repo_id)
            repo.error_message = "Generating AI embeddings..."
            await db.commit()
            try:
                await _generate_embeddings_for_repo(repo_id, db)
                repo.processing_progress = 90.0
                repo.error_message = "Embeddings generated successfully"
                await db.commit()
                logger.info("[%s] ✓ Embeddings generated", repo_id)
            except Exception as e:
                logger.warning("[%s]   Embedding generation failed: %s", repo_id, e)
                repo.processing_progress = 85.0
                repo.error_message = "Embeddings generation failed (partial completion)"
                await db.commit()

            # ── Step 6: Build file tree and update metadata ──
            logger.info("[%s]  Building file tree and dependency graph...", repo_id)
            repo.error_message = "Building file tree..."
            await db.commit()
            file_tree = build_file_tree(repo_path)
            meta = repo.metadata_jsonb or {}
            meta["total_files"] = total_files
            meta["total_lines"] = sum(
                c["end_line"] for c in all_chunks if c.get("chunk_type") == "file"
            )
            meta["file_tree"] = file_tree  # Store file tree
            repo.metadata_jsonb = meta

            # ── Done ─────────────────────────────────────
            repo.status = "completed"
            repo.processing_progress = 100.0
            repo.error_message = "Analysis complete"
            await db.commit()

            logger.info("[%s]  Analysis completed! %d files, %d chunks processed", repo_id, total_files, len(all_chunks))

        finally:
            # Clean up temp directory
            shutil.rmtree(tmp_dir, ignore_errors=True)

    await engine.dispose()


async def _update_status(repo_id: str, status: str, progress: float, message: str = None):
    """Update repo status (used in error paths)."""
    engine = create_async_engine(settings.DATABASE_URL, pool_size=2)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if repo:
            repo.status = status
            repo.processing_progress = progress
            repo.error_message = message
            await db.commit()

    await engine.dispose()
