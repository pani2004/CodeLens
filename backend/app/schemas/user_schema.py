"""User Pydantic schemas — matches frontend User & AuthTokens interfaces."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request Schemas ──────────────────────────────────────
class GitHubCallbackRequest(BaseModel):
    code: str = Field(..., description="GitHub OAuth authorization code")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Response Schemas ─────────────────────────────────────
class UserResponse(BaseModel):
    id: str
    github_id: str
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_user(cls, user) -> "UserResponse":
        return cls(
            id=str(user.id),
            github_id=user.github_id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            created_at=user.created_at.isoformat() if user.created_at else "",
        )


class TokenResponse(BaseModel):
    """Matches frontend AuthTokens interface."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthCallbackResponse(BaseModel):
    """Matches frontend handleGitHubCallback return."""
    user: UserResponse
    tokens: TokenResponse
