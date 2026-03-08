"""Chat controller — handles chat requests, history management."""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.models.user import User
from app.models.repository import Repository
from app.models.chat_history import ChatHistory
from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessageSchema,
    SuggestedPromptsResponse,
)
from app.services.chat_service import chat_stream, chat_sync, get_suggested_prompts
from app.middleware.auth_middleware import check_repo_ownership

logger = logging.getLogger("codelens.chat_ctrl")


async def handle_chat_stream(
    request: ChatRequest,
    user: User,
    db: AsyncSession,
) -> StreamingResponse:
    """Handle streaming chat request — returns SSE response."""
    # Verify repo access
    repo = await _get_repo_or_403(request.repo_id, user, db)

    # Load existing history if not provided
    history = None
    if request.history:
        history = [msg.model_dump() for msg in request.history]
    else:
        history = await _load_history(user.id, request.repo_id, db)

    # Stream the response
    async def event_generator():
        full_response = ""
        sources = []

        async for chunk in chat_stream(
            query=request.message,
            repo_id=request.repo_id,
            user_id=str(user.id),
            db=db,
            history=history,
            file_path=request.file_path,
        ):
            yield chunk
            # Accumulate response for history
            try:
                data_str = chunk.strip()
                if data_str.startswith("data: ") and data_str != "data: [DONE]":
                    parsed = json.loads(data_str[6:])
                    if "content" in parsed:
                        full_response += parsed["content"]
                    if "sources" in parsed:
                        sources = parsed["sources"]
            except (json.JSONDecodeError, IndexError):
                pass

        # Save to history after streaming completes
        await _save_message(user.id, request.repo_id, "user", request.message, db)
        await _save_message(user.id, request.repo_id, "assistant", full_response, db, sources)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def handle_chat_sync(
    request: ChatRequest,
    user: User,
    db: AsyncSession,
) -> ChatResponse:
    """Handle non-streaming chat request."""
    await _get_repo_or_403(request.repo_id, user, db)

    history = None
    if request.history:
        history = [msg.model_dump() for msg in request.history]
    else:
        history = await _load_history(user.id, request.repo_id, db)

    result = await chat_sync(
        query=request.message,
        repo_id=request.repo_id,
        user_id=str(user.id),
        db=db,
        history=history,
        file_path=request.file_path,
    )

    # Save to history
    await _save_message(user.id, request.repo_id, "user", request.message, db)
    await _save_message(user.id, request.repo_id, "assistant", result["message"], db, result.get("sources"))

    return ChatResponse(**result)


async def get_chat_history(
    repo_id: str,
    user: User,
    db: AsyncSession,
) -> ChatHistoryResponse:
    """Get chat history for a repository."""
    await _get_repo_or_403(repo_id, user, db)

    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == user.id,
            ChatHistory.repo_id == repo_id,
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        return ChatHistoryResponse(messages=[])

    messages = []
    for msg in (chat.messages_jsonb or []):
        messages.append(ChatMessageSchema(
            id=msg.get("id", str(uuid.uuid4())),
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp", ""),
            sources=msg.get("sources"),
        ))

    return ChatHistoryResponse(messages=messages)


async def clear_chat_history(
    repo_id: str,
    user: User,
    db: AsyncSession,
) -> dict:
    """Clear chat history for a repository."""
    await _get_repo_or_403(repo_id, user, db)

    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == user.id,
            ChatHistory.repo_id == repo_id,
        )
    )
    chat = result.scalar_one_or_none()

    if chat:
        await db.delete(chat)

    return {"message": "Chat history cleared"}


async def handle_suggested_prompts(
    repo_id: str,
    user: User,
    db: AsyncSession,
) -> SuggestedPromptsResponse:
    """Get suggested chat prompts for a repository."""
    await _get_repo_or_403(repo_id, user, db)
    prompts = await get_suggested_prompts(repo_id, db)
    return SuggestedPromptsResponse(prompts=prompts)


# ── Helpers ──────────────────────────────────────────────
async def _get_repo_or_403(repo_id: str, user: User, db: AsyncSession) -> Repository:
    """Verify repository exists and user has access."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    check_repo_ownership(user, repo.user_id)
    return repo


async def _load_history(user_id, repo_id: str, db: AsyncSession) -> list[dict]:
    """Load last 10 messages from history."""
    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == user_id,
            ChatHistory.repo_id == repo_id,
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        return []
    return (chat.messages_jsonb or [])[-10:]


async def _save_message(
    user_id,
    repo_id: str,
    role: str,
    content: str,
    db: AsyncSession,
    sources: Optional[list] = None,
) -> None:
    """Save a message to chat history."""
    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == user_id,
            ChatHistory.repo_id == repo_id,
        )
    )
    chat = result.scalar_one_or_none()

    message = {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if sources:
        message["sources"] = sources

    if chat:
        messages = list(chat.messages_jsonb or [])
        messages.append(message)
        chat.messages_jsonb = messages
    else:
        chat = ChatHistory(
            user_id=user_id,
            repo_id=repo_id,
            messages_jsonb=[message],
        )
        db.add(chat)
