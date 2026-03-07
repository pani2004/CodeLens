"""Analysis controller — dependency graphs and execution flows."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.models.repository import Repository
from app.schemas.repo_schema import DependencyGraph, ExecutionFlow
from app.services.graph_service import build_dependency_graph
from app.services.flow_service import get_execution_flows
from app.middleware.auth_middleware import check_repo_ownership

logger = logging.getLogger("codelens.analysis")


async def get_dependency_graph(
    repo_id: str,
    user: User,
    db: AsyncSession,
    language: str = None,
    depth: int = None,
) -> dict:
    """Get dependency graph for a repository."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    graph_data = await build_dependency_graph(str(repo.id), db)

    # Apply filters
    if language:
        graph_data["nodes"] = [n for n in graph_data["nodes"] if n["language"] == language]
        valid_ids = {n["id"] for n in graph_data["nodes"]}
        graph_data["edges"] = [e for e in graph_data["edges"] if e["source"] in valid_ids and e["target"] in valid_ids]
        graph_data["metrics"]["total_nodes"] = len(graph_data["nodes"])
        graph_data["metrics"]["total_edges"] = len(graph_data["edges"])

    return graph_data


async def get_execution_flows_handler(
    repo_id: str,
    user: User,
    db: AsyncSession,
) -> list[dict]:
    """Get execution flows for a repository."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    flows = await get_execution_flows(str(repo.id), db)
    return flows


async def get_flow_detail(
    repo_id: str,
    flow_id: str,
    user: User,
    db: AsyncSession,
) -> dict:
    """Get a specific execution flow by ID."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    flows = await get_execution_flows(str(repo.id), db)
    for flow in flows:
        if flow["id"] == flow_id:
            return flow

    raise HTTPException(status_code=404, detail="Flow not found")


# ── Helpers ──────────────────────────────────────────────
async def _get_repo_or_404(repo_id: str, db: AsyncSession) -> Repository:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo
