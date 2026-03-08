"""Chat routes """

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit_middleware import limiter
from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    SuggestedPromptsResponse,
)
from app.controllers import chat_controller

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
@limiter.limit("50/hour")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /chat (streaming SSE)
    Frontend: sendChatMessage(repoId, message, filePath?) → SSE stream
    Data format: data: {"content": "..."} / data: {"sources": [...]} / data: [DONE]
    """
    return await chat_controller.handle_chat_stream(body, user, db)


@router.post("/sync", response_model=ChatResponse)
async def chat_sync(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /chat/sync (non-streaming)
    Frontend: sendChatMessageSync(request) → ChatResponse
    """
    return await chat_controller.handle_chat_sync(body, user, db)


@router.get("/history/{repo_id}", response_model=ChatHistoryResponse)
async def get_history(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /chat/history/{repo_id}
    Frontend: getChatHistory(repoId) → { messages }
    """
    return await chat_controller.get_chat_history(repo_id, user, db)


@router.delete("/history/{repo_id}")
async def clear_history(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    DELETE /chat/history/{repo_id}
    Frontend: clearChatHistory(repoId)
    """
    return await chat_controller.clear_chat_history(repo_id, user, db)


@router.get("/prompts/{repo_id}", response_model=SuggestedPromptsResponse)
async def get_prompts(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /chat/prompts/{repo_id}
    Frontend: getSuggestedPrompts(repoId) → { prompts }
    """
    return await chat_controller.handle_suggested_prompts(repo_id, user, db)
