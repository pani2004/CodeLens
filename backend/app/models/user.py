"""User model — mirrors frontend User interface."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    access_token_encrypted = Column(Text, nullable=True)  # Fernet-encrypted GitHub token

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.username}>"
