"""Authentication controller — handles GitHub OAuth, token management."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user_schema import UserResponse, TokenResponse, AuthCallbackResponse
from app.services.github_service import (
    get_authorization_url,
    exchange_code_for_token,
    get_user_info,
)
from app.utils.jwt import create_access_token, create_refresh_token, verify_refresh_token
from app.utils.crypto import encrypt_token
from app.utils.audit import log_auth_event


async def github_login() -> dict:
    """Generate GitHub OAuth authorization URL."""
    state = str(uuid.uuid4())
    url = get_authorization_url(state=state)
    log_auth_event("github_login_initiated")
    return {"authorization_url": url}


async def github_callback(code: str, db: AsyncSession) -> AuthCallbackResponse:
    """
    Handle GitHub OAuth callback:
    1. Exchange code for GitHub access token
    2. Fetch GitHub user info
    3. Create or update user in DB
    4. Return JWT tokens
    """
    # Exchange code for token
    github_token = await exchange_code_for_token(code)

    # Fetch user info from GitHub
    github_user = await get_user_info(github_token)

    # Find or create user
    result = await db.execute(
        select(User).where(User.github_id == github_user["github_id"])
    )
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = github_user["username"]
        user.email = github_user["email"]
        user.avatar_url = github_user["avatar_url"]
        user.access_token_encrypted = encrypt_token(github_token)
        log_auth_event("user_login", user_id=str(user.id))
    else:
        # Create new user
        user = User(
            github_id=github_user["github_id"],
            username=github_user["username"],
            email=github_user["email"],
            avatar_url=github_user["avatar_url"],
            access_token_encrypted=encrypt_token(github_token),
        )
        db.add(user)
        await db.flush()  # Get user.id
        log_auth_event("user_created", user_id=str(user.id))

    # Create JWT tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    user_response = UserResponse.from_orm_user(user)
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    return AuthCallbackResponse(user=user_response, tokens=token_response)


async def refresh_token(refresh_token_str: str, db: AsyncSession) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    user_id = verify_refresh_token(refresh_token_str)
    if not user_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))

    log_auth_event("token_refreshed", user_id=str(user.id))

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


async def get_me(user: User) -> UserResponse:
    """Get current authenticated user."""
    return UserResponse.from_orm_user(user)


async def logout(user: User) -> dict:
    """Handle logout (token invalidation would happen client-side)."""
    log_auth_event("user_logout", user_id=str(user.id))
    return {"message": "Logged out successfully"}
