"""Chat Pydantic schemas — matches frontend ChatMessage, ChatRequest, ChatResponse interfaces."""

from pydantic import BaseModel, Field
from typing import Optional, List


# ── Sub-schemas ──────────────────────────────────────────
class CodeSource(BaseModel):
    """Matches frontend CodeSource interface."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    relevance_score: Optional[float] = None


class ChatMessageSchema(BaseModel):
    """Matches frontend ChatMessage interface."""
    id: str
    role: str  # user | assistant
    content: str
    timestamp: str
    sources: Optional[List[CodeSource]] = None


# ── Request Schemas ──────────────────────────────────────
class ChatRequest(BaseModel):
    """Matches frontend ChatRequest interface."""
    repo_id: str
    message: str
    file_path: Optional[str] = None
    history: Optional[List[ChatMessageSchema]] = None


# ── Response Schemas ─────────────────────────────────────
class ChatResponse(BaseModel):
    """Matches frontend ChatResponse interface."""
    message: str
    sources: List[CodeSource] = []
    model: str = "gemini-1.5-flash"


class ChatHistoryResponse(BaseModel):
    """Matches frontend getChatHistory return."""
    messages: List[ChatMessageSchema]


class SuggestedPromptsResponse(BaseModel):
    """Matches frontend getSuggestedPrompts return."""
    prompts: List[str]
