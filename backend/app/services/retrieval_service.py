"""Retrieval service — vector + full-text hybrid search with reranking."""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, func, cast
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

from app.models.code_chunk import CodeChunk
from app.services.embedding_service import generate_embedding

logger = logging.getLogger("codelens.retrieval")


async def vector_search(
    query: str,
    repo_id: str,
    db: AsyncSession,
    top_k: int = 15,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    chunk_type: Optional[str] = None,
) -> list[dict]:
    """
    Cosine-similarity search using pgvector.
    Returns top_k code chunks ranked by relevance.
    """
    # Generate query embedding
    query_embedding = await generate_embedding(query)

    # Build base query with cosine distance
    # Use pgvector's cosine distance operator: embedding <=> query_vector
    distance = CodeChunk.embedding.cosine_distance(query_embedding)
    similarity = 1 - distance
    
    stmt = (
        select(
            CodeChunk.id,
            CodeChunk.file_path,
            CodeChunk.chunk_type,
            CodeChunk.content,
            CodeChunk.language,
            CodeChunk.start_line,
            CodeChunk.end_line,
            CodeChunk.metadata_jsonb,
            similarity.label("similarity")
        )
        .where(
            and_(
                CodeChunk.repo_id == repo_id,
                CodeChunk.embedding.isnot(None)
            )
        )
        .order_by(distance)
        .limit(top_k)
    )

    # Add optional filters
    if file_path:
        stmt = stmt.where(CodeChunk.file_path.ilike(f"%{file_path}%"))
    if language:
        stmt = stmt.where(CodeChunk.language == language)
    if chunk_type:
        stmt = stmt.where(CodeChunk.chunk_type == chunk_type)

    result = await db.execute(stmt)
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "file_path": row.file_path,
            "chunk_type": row.chunk_type,
            "content": row.content,
            "language": row.language,
            "start_line": row.start_line,
            "end_line": row.end_line,
            "metadata": row.metadata_jsonb or {},
            "relevance_score": float(row.similarity),
        }
        for row in rows
    ]


async def hybrid_search(
    query: str,
    repo_id: str,
    db: AsyncSession,
    top_k: int = 15,
    file_path: Optional[str] = None,
) -> list[dict]:
    """
    Combine vector search with PostgreSQL full-text search for better results.
    Uses RRF (Reciprocal Rank Fusion) to merge rankings.
    """
    # Vector search results
    vector_results = await vector_search(query, repo_id, db, top_k=top_k * 2, file_path=file_path)

    # Full-text search
    fts_query = text("""
        SELECT id, file_path, chunk_type, content, language, start_line, end_line,
               metadata_jsonb,
               ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) AS rank
        FROM code_chunks
        WHERE repo_id = :repo_id
          AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)
    result = await db.execute(fts_query, {"query": query, "repo_id": repo_id, "limit": top_k * 2})
    fts_rows = result.fetchall()

    fts_results = [
        {
            "id": str(row.id),
            "file_path": row.file_path,
            "chunk_type": row.chunk_type,
            "content": row.content,
            "language": row.language,
            "start_line": row.start_line,
            "end_line": row.end_line,
            "metadata": row.metadata_jsonb or {},
            "relevance_score": float(row.rank),
        }
        for row in fts_rows
    ]

    # RRF fusion
    k = 60  # RRF constant
    scores: dict[str, float] = {}
    all_chunks: dict[str, dict] = {}

    for rank, chunk in enumerate(vector_results):
        chunk_id = chunk["id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        all_chunks[chunk_id] = chunk

    for rank, chunk in enumerate(fts_results):
        chunk_id = chunk["id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        all_chunks[chunk_id] = chunk

    # Sort by fused score and return top_k
    sorted_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]

    results = []
    for chunk_id in sorted_ids:
        chunk = all_chunks[chunk_id]
        chunk["relevance_score"] = scores[chunk_id]
        results.append(chunk)

    return results
