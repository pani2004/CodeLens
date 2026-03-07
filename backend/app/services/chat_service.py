"""Chat service — LangChain RAG pipeline with Gemini for codebase Q&A."""

import json
import logging
import asyncio
from typing import AsyncGenerator, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.retrieval_service import hybrid_search
from app.services.embedding_service import generate_embedding

settings = get_settings()
logger = logging.getLogger("codelens.chat")

# ── System prompt ────────────────────────────────────────
SYSTEM_PROMPT = """You are CodeLens AI, an expert code analysis assistant. You help developers understand codebases by answering questions about code structure, functionality, and architecture.

## Guidelines:
1. **Be precise**: Reference specific files, functions, and line numbers from the context provided.
2. **Be thorough**: Explain not just what the code does, but why and how it connects to the broader codebase.
3. **Use code blocks properly** - THIS IS CRITICAL:
   - When listing multiple related items (service names, components, functions, variables, etc.), put them ALL in ONE SINGLE code block
   - NEVER split a list into multiple separate code blocks
   - Example: If listing 4 services, write them as:
     ```
     elasticsearch
     kibana
     chroma
     postgresql
     ```
   - NOT as 4 separate code blocks for each service
   - Only use separate code blocks when showing code from completely different files or different programming languages
4. **Cite sources**: Always mention which files your answer is based on.
5. **Be honest**: If the provided context doesn't contain enough information, say so clearly.
6. **Focus on functionality**: Prioritize explaining business logic, algorithms, data flow, and architecture. Skip detailed CSS/styling explanations unless explicitly asked. Instead of explaining CSS classes, focus on the component's purpose and behavior.
7. **Security**: Never execute code, never reveal API keys, never modify files.

## Context from the codebase:
{context}

## Instructions:
Answer the user's question based on the codebase context above. Focus on core functionality, business logic, and architecture rather than styling details. 

IMPORTANT: When listing multiple related items (services, components, functions, etc.), you MUST put them all in a SINGLE code block together, NOT in separate blocks. If the context doesn't contain relevant information, state that clearly and suggest what the user might look for.
"""


# ── Prompt injection detection ───────────────────────────
SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "ignore above instructions",
    "disregard your instructions",
    "forget your instructions",
    "you are now",
    "act as if",
    "pretend you are",
    "system prompt",
    "reveal your prompt",
    "what are your instructions",
]


def detect_prompt_injection(message: str) -> bool:
    """Check for common prompt injection patterns."""
    lower = message.lower()
    return any(pattern in lower for pattern in SUSPICIOUS_PATTERNS)


# ── LLM initialization ──────────────────────────────────
def get_llm(streaming: bool = False) -> ChatGoogleGenerativeAI:
    """Get Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        max_output_tokens=4096,
        streaming=streaming,
    )


# ── Format context ───────────────────────────────────────
def format_context(chunks: list[dict]) -> str:
    """Format retrieved code chunks into a context string."""
    if not chunks:
        return "No relevant code found in the repository."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        part = f"### Source {i}: `{chunk['file_path']}` (lines {chunk['start_line']}-{chunk['end_line']})\n"
        part += f"**Type**: {chunk['chunk_type']} | **Language**: {chunk['language']}\n"
        part += f"```{chunk['language']}\n{chunk['content']}\n```\n"
        parts.append(part)

    return "\n".join(parts)


def format_sources(chunks: list[dict]) -> list[dict]:
    """Format chunks into CodeSource objects for the frontend."""
    return [
        {
            "file_path": c["file_path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "content": c["content"][:500],  # Truncate for response size
            "relevance_score": c.get("relevance_score", 0),
        }
        for c in chunks
    ]


# ── Chat (streaming) ────────────────────────────────────
async def chat_stream(
    query: str,
    repo_id: str,
    user_id: str,
    db: AsyncSession,
    history: Optional[list[dict]] = None,
    file_path: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Streaming RAG chat — yields Server-Sent Event data chunks.
    Used by POST /chat endpoint.
    """
    from app.utils.audit import log_security_event

    # Check for prompt injection
    if detect_prompt_injection(query):
        log_security_event("prompt_injection_attempt", {"query": query[:100], "user_id": user_id})
        yield f'data: {json.dumps({"content": "I cannot process this request. Please rephrase your question about the codebase."})}\n\n'
        yield "data: [DONE]\n\n"
        return

    # Retrieve relevant code chunks
    chunks = await hybrid_search(query, repo_id, db, top_k=10, file_path=file_path)
    context = format_context(chunks)
    sources = format_sources(chunks)

    # Build messages
    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]

    # Add conversation history (last 5 exchanges)
    if history:
        for msg in history[-10:]:  # Last 5 exchanges = 10 messages
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    # Stream response
    llm = get_llm(streaming=True)

    # Yield sources first
    yield f'data: {json.dumps({"sources": sources})}\n\n'

    try:
        logger.info(f"Starting LLM stream for query: {query[:50]}...")
        chunk_count = 0
        async for chunk in llm.astream(messages):
            if chunk.content:
                chunk_count += 1
                logger.debug(f"LLM chunk {chunk_count}: {chunk.content[:100]}")
                yield f'data: {json.dumps({"content": chunk.content})}\n\n'
        logger.info(f"LLM stream complete. Total chunks: {chunk_count}")
    except Exception as e:
        logger.error("Chat stream error: %s", e, exc_info=True)
        yield f'data: {json.dumps({"content": f"Error generating response: {str(e)}"})}\n\n'

    yield "data: [DONE]\n\n"


# ── Chat (non-streaming) ────────────────────────────────
async def chat_sync(
    query: str,
    repo_id: str,
    user_id: str,
    db: AsyncSession,
    history: Optional[list[dict]] = None,
    file_path: Optional[str] = None,
) -> dict:
    """Non-streaming chat for the sync endpoint."""
    from app.utils.audit import log_security_event

    if detect_prompt_injection(query):
        log_security_event("prompt_injection_attempt", {"query": query[:100], "user_id": user_id})
        return {
            "message": "I cannot process this request. Please rephrase your question about the codebase.",
            "sources": [],
            "model": settings.GEMINI_MODEL,
        }

    chunks = await hybrid_search(query, repo_id, db, top_k=10, file_path=file_path)
    context = format_context(chunks)
    sources = format_sources(chunks)

    messages = [SystemMessage(content=SYSTEM_PROMPT.format(context=context))]
    if history:
        for msg in history[-10:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=query))

    llm = get_llm(streaming=False)
    response = await llm.ainvoke(messages)

    return {
        "message": response.content,
        "sources": sources,
        "model": settings.GEMINI_MODEL,
    }


# ── Repository summary generation ───────────────────────
async def generate_summary(repo_id: str, db: AsyncSession) -> dict:
    """Generate a structured summary of the repository using Gemini."""
    from app.models.code_chunk import CodeChunk
    from sqlalchemy import select

    # Get key files (README, entry points, config files)
    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .where(
            CodeChunk.file_path.in_([
                "README.md", "readme.md", "README.rst",
                "main.py", "app.py", "index.js", "index.ts",
                "package.json", "requirements.txt", "pyproject.toml",
                "Cargo.toml", "go.mod", "pom.xml",
            ])
        )
        .limit(10)
    )
    key_chunks = result.scalars().all()

    # Also get a sample of other chunks for broader understanding
    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .where(CodeChunk.chunk_type.in_(["file", "class"]))
        .limit(20)
    )
    sample_chunks = result.scalars().all()

    all_chunks = list(key_chunks) + list(sample_chunks)

    if not all_chunks:
        return {
            "purpose": "Unable to determine — no code chunks found",
            "features": [],
            "tech_stack": [],
            "architecture": "Unknown",
            "key_files": [],
        }

    # Build context
    context_parts = []
    for chunk in all_chunks:
        context_parts.append(f"File: {chunk.file_path}\n```\n{chunk.content[:2000]}\n```")

    context = "\n\n".join(context_parts)

    prompt = f"""Analyze this codebase and provide a structured summary.

{context}

Respond in this exact JSON format:
{{
    "purpose": "A 1-2 sentence description of what this project does",
    "features": ["feature1", "feature2", "feature3"],
    "tech_stack": ["technology1", "technology2"],
    "architecture": "Brief description of the architecture pattern",
    "key_files": ["file1.py", "file2.js"]
}}

Only respond with valid JSON, no markdown or explanation."""

    llm = get_llm(streaming=False)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        # Parse the JSON response
        summary = json.loads(response.content.strip().strip("```json").strip("```"))
        return summary
    except json.JSONDecodeError:
        logger.error("Failed to parse summary JSON: %s", response.content[:200])
        return {
            "purpose": response.content[:500],
            "features": [],
            "tech_stack": [],
            "architecture": "See purpose for details",
            "key_files": [],
        }


# ── Suggested prompts ───────────────────────────────────
async def get_suggested_prompts(repo_id: str, db: AsyncSession) -> list[str]:
    """Generate context-aware suggested prompts for a repository."""
    from app.models.repository import Repository
    from sqlalchemy import select

    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()

    if not repo:
        return _default_prompts()

    meta = repo.metadata_jsonb or {}
    language = repo.language or "the codebase"

    prompts = [
        f"What does this {language} project do?",
        "Explain the main architecture and design patterns",
        "What are the entry points of this application?",
        "List and explain the key dependencies",
        "How does error handling work in this codebase?",
    ]

    if meta.get("tech_stack"):
        stack = meta["tech_stack"]
        if any("react" in t.lower() for t in stack):
            prompts.append("Explain the component hierarchy")
        if any("express" in t.lower() or "fastapi" in t.lower() for t in stack):
            prompts.append("List all API endpoints and their handlers")

    return prompts[:6]


def _default_prompts() -> list[str]:
    return [
        "What does this project do?",
        "Explain the main architecture",
        "Show me the entry points",
        "What are the key dependencies?",
        "How does authentication work?",
    ]
