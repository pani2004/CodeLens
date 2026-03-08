"""Repository model — mirrors frontend Repository interface."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Float, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_url = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    star_count = Column(Integer, default=0)
    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending | processing | completed | failed
    processing_progress = Column(Float, default=0.0)  # 0-100
    error_message = Column(Text, nullable=True)
    metadata_jsonb = Column(JSONB, default=dict)  # summary, tech_stack, key_files, etc.

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="repositories")
    code_chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="repository", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_repositories_user_id", "user_id"),
        Index("ix_repositories_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Repository {self.name} ({self.status})>"
