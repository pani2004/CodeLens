"""Repository Pydantic schemas — matches frontend Repository, RepositorySummary interfaces."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Any
from datetime import datetime


# ── Request Schemas ──────────────────────────────────────
class AnalyzeRepoRequest(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL")


# ── Sub-schemas ──────────────────────────────────────────
class RepositoryMetadata(BaseModel):
    summary: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    key_files: Optional[List[str]] = None
    entry_points: Optional[List[str]] = None
    architecture: Optional[str] = None
    total_files: Optional[int] = None
    total_lines: Optional[int] = None
    file_tree: Optional[List[dict]] = None  # File explorer tree


class FileNode(BaseModel):
    id: str
    path: str
    name: str
    type: str  # file | directory
    language: Optional[str] = None
    size: Optional[int] = None
    children: Optional[List["FileNode"]] = None


class DependencyNode(BaseModel):
    id: str
    label: str
    type: str  # file | module | package
    language: str
    size: int
    complexity: Optional[int] = None


class DependencyEdge(BaseModel):
    source: str
    target: str
    type: str  # import | export | call
    weight: int
    label: Optional[str] = None


class DependencyGraph(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    entry_points: List[str]
    metrics: dict


class FlowStep(BaseModel):
    order: int
    type: str  # middleware | handler | database | external_api | response
    file_path: str
    function_name: str
    line_number: int
    description: str


class FlowNode(BaseModel):
    id: str
    type: str  # start | end | process | decision
    label: str
    description: Optional[str] = None


class FlowEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None
    type: Optional[str] = None


class ExecutionFlow(BaseModel):
    id: str
    route: str
    method: str
    description: str
    steps: List[FlowStep]
    complexity: int
    nodes: List[FlowNode]
    edges: List[FlowEdge]


# ── Response Schemas ─────────────────────────────────────
class RepositoryResponse(BaseModel):
    """Matches frontend Repository interface."""
    id: str
    user_id: str
    github_url: str
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    star_count: int = 0
    status: str = "pending"
    processing_progress: float = 0.0
    error_message: Optional[str] = None
    metadata: RepositoryMetadata = RepositoryMetadata()
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_repo(cls, repo) -> "RepositoryResponse":
        meta = repo.metadata_jsonb or {}
        return cls(
            id=str(repo.id),
            user_id=str(repo.user_id),
            github_url=repo.github_url,
            name=repo.name,
            description=repo.description,
            language=repo.language,
            star_count=repo.star_count or 0,
            status=repo.status,
            processing_progress=repo.processing_progress or 0.0,
            error_message=repo.error_message,
            metadata=RepositoryMetadata(**meta) if meta else RepositoryMetadata(),
            created_at=repo.created_at.isoformat() if repo.created_at else "",
            updated_at=repo.updated_at.isoformat() if repo.updated_at else None,
        )


class AnalyzeRepoResponse(BaseModel):
    repo_id: str
    task_id: str


class RepoStatusResponse(BaseModel):
    status: str
    progress: float
    message: Optional[str] = None


class RepositorySummaryResponse(BaseModel):
    """Matches frontend RepositorySummary interface."""
    repository: RepositoryResponse
    purpose: str
    features: List[str]
    tech_stack: List[str]
    architecture: str
    key_files: List[str]
    fileTree: Optional[List[FileNode]] = None
    dependencyGraph: Optional[DependencyGraph] = None
    executionFlows: Optional[List[ExecutionFlow]] = None


class PaginatedRepoResponse(BaseModel):
    """Matches frontend PaginatedResponse<Repository>."""
    data: List[RepositoryResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class GitHubRepoItem(BaseModel):
    name: str
    full_name: str
    url: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0


class UsageQuotaResponse(BaseModel):
    """Matches frontend UsageQuota interface."""
    chat_requests: dict  # {used, limit}
    repos_analyzed: dict  # {used, limit}
    storage: dict  # {used, limit}
    tier: str  # free | pro
