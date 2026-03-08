"""Authentication routes — matches frontend lib/api/auth.ts endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit_middleware import limiter
from app.schemas.user_schema import (
    GitHubCallbackRequest,
    RefreshTokenRequest,
    UserResponse,
    AuthCallbackResponse,
    TokenResponse,
)
from app.controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github/login")
@limiter.limit("5/15minutes")
async def github_login(request: Request):
    """
    GET /auth/github/login
    Frontend: initiateGitHubLogin() → { authorization_url }
    """
    return await auth_controller.github_login()


@router.post("/github/callback", response_model=AuthCallbackResponse)
async def github_callback(
    body: GitHubCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /auth/github/callback
    Frontend: handleGitHubCallback(code) → { user, tokens }
    """
    return await auth_controller.github_callback(body.code, db)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    GET /auth/me
    Frontend: getCurrentUser() → User
    """
    return await auth_controller.get_me(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /auth/refresh
    Frontend: refreshAccessToken(refreshToken) → AuthTokens
    """
    return await auth_controller.refresh_token(body.refresh_token, db)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    POST /auth/logout
    Frontend: logout()
    """
    return await auth_controller.logout(user)
