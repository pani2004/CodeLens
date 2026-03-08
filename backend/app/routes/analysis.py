"""Analysis routes — dependency graphs and execution flows."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.middleware.auth_middleware import get_current_user
from app.controllers import analysis_controller

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/{repo_id}/graph")
async def get_dependency_graph(
    repo_id: str,
    language: Optional[str] = Query(None),
    depth: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /analysis/{repo_id}/graph?language=python&depth=3
    Returns DependencyGraph data for React Flow visualization.
    """
    return await analysis_controller.get_dependency_graph(repo_id, user, db, language, depth)


@router.get("/{repo_id}/flows")
async def get_execution_flows(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /analysis/{repo_id}/flows
    Returns ExecutionFlow[] for React Flow visualization.
    """
    return await analysis_controller.get_execution_flows_handler(repo_id, user, db)


@router.get("/{repo_id}/flows/{flow_id}")
async def get_flow_detail(
    repo_id: str,
    flow_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /analysis/{repo_id}/flows/{flow_id}
    Returns a single ExecutionFlow detail.
    """
    return await analysis_controller.get_flow_detail(repo_id, flow_id, user, db)
