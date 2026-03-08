"""Repository routes — matches frontend lib/api/repos.ts endpoints."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit_middleware import limiter
from app.schemas.repo_schema import (
    AnalyzeRepoRequest,
    AnalyzeRepoResponse,
    RepositoryResponse,
    RepoStatusResponse,
    RepositorySummaryResponse,
    PaginatedRepoResponse,
    UsageQuotaResponse,
)
from app.controllers import repo_controller

router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("", response_model=PaginatedRepoResponse)
async def get_repositories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos?page=1&page_size=20
    Frontend: getRepositories(page, pageSize) → PaginatedResponse<Repository>
    """
    return await repo_controller.get_repositories(user, db, page, page_size)


@router.get("/github/list")
async def get_github_repos(user: User = Depends(get_current_user)):
    """
    GET /repos/github/list
    Frontend: getGitHubRepositories() → GitHubRepoItem[]
    """
    return await repo_controller.get_github_repos(user)


@router.get("/quota", response_model=UsageQuotaResponse)
async def get_quota(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos/quota
    Frontend: UsageQuota
    """
    return await repo_controller.get_usage_quota(user, db)


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos/{repo_id}
    Frontend: getRepository(repoId) → Repository
    """
    return await repo_controller.get_repository(repo_id, user, db)


@router.post("/analyze", response_model=AnalyzeRepoResponse)
@limiter.limit("5/day")
async def analyze_repository(
    body: AnalyzeRepoRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /repos/analyze { github_url }
    Frontend: analyzeRepository(githubUrl) → { repo_id, task_id }
    """
    return await repo_controller.analyze_repository(body.github_url, user, db)


@router.get("/{repo_id}/status", response_model=RepoStatusResponse)
async def get_repository_status(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos/{repo_id}/status
    Frontend: getRepositoryStatus(repoId) → { status, progress, message? }
    """
    return await repo_controller.get_repository_status(repo_id, user, db)


@router.get("/{repo_id}/summary", response_model=RepositorySummaryResponse)
async def get_repository_summary(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos/{repo_id}/summary
    Frontend: getRepositorySummary(repoId) → RepositorySummary
    """
    return await repo_controller.get_repository_summary(repo_id, user, db)


@router.post("/{repo_id}/summary/regenerate", response_model=RepositorySummaryResponse)
async def regenerate_summary(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /repos/{repo_id}/summary/regenerate
    Frontend: regenerateSummary(repoId) → RepositorySummary
    """
    return await repo_controller.regenerate_summary(repo_id, user, db)


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    DELETE /repos/{repo_id}
    Frontend: deleteRepository(repoId)
    """
    return await repo_controller.delete_repository(repo_id, user, db)


@router.get("/{repo_id}/files")
async def get_file_content(
    repo_id: str,
    file_path: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /repos/{repo_id}/files?file_path=...
    Frontend: getFileContent(repoId, filePath) → FileContentResponse
    """
    return await repo_controller.get_file_content(repo_id, file_path, user, db)
