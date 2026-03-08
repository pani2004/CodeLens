"""ChatHistory model — stores conversation threads per user per repo."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    messages_jsonb = Column(JSONB, default=list)  # [{role, content, timestamp, sources}]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="chat_histories")
    repository = relationship("Repository", back_populates="chat_histories")

    __table_args__ = (
        Index("ix_chat_histories_user_repo", "user_id", "repo_id"),
    )

    def __repr__(self) -> str:
        return f"<ChatHistory user={self.user_id} repo={self.repo_id}>"
