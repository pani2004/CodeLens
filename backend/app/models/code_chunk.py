"""CodeChunk model — stores parsed code segments with vector embeddings."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.database import Base


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    chunk_type = Column(String(20), nullable=False)  # file | class | function | block
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)
    start_line = Column(Integer, nullable=False, default=1)
    end_line = Column(Integer, nullable=False, default=1)
    embedding = Column(Vector(3072), nullable=True)  # Gemini embedding-001 = 3072 dims
    metadata_jsonb = Column(JSONB, default=dict)  # symbols, imports, exports

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    repository = relationship("Repository", back_populates="code_chunks")

    __table_args__ = (
        Index("ix_code_chunks_repo_id", "repo_id"),
        Index("ix_code_chunks_file_path", "file_path"),
        Index("ix_code_chunks_chunk_type", "chunk_type"),
        # Note: No vector index for 3072-dim embeddings (pgvector limit: 2000 dims)
        # Queries will use brute-force search (acceptable for typical repo sizes)
        Index("ix_code_chunks_metadata", "metadata_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<CodeChunk {self.file_path}:{self.start_line}-{self.end_line}>"
