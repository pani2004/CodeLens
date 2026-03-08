"""Repository controller — handles CRUD, analysis orchestration, summaries."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.repository import Repository
from app.models.code_chunk import CodeChunk
from app.schemas.repo_schema import (
    RepositoryResponse,
    AnalyzeRepoResponse,
    RepoStatusResponse,
    RepositorySummaryResponse,
    PaginatedRepoResponse,
    GitHubRepoItem,
    UsageQuotaResponse,
)
from app.services.github_service import get_repo_info, list_user_repos
from app.services.chat_service import generate_summary
from app.services.parser_service import build_file_tree
from app.utils.validators import validate_github_url, parse_github_url
from app.utils.crypto import decrypt_token
from app.utils.audit import log_repo_access
from app.middleware.auth_middleware import check_repo_ownership

logger = logging.getLogger("codelens.repo")


async def get_repositories(
    user: User,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedRepoResponse:
    """Get paginated repositories for the current user."""
    offset = (page - 1) * page_size

    # Count total
    count_result = await db.execute(
        select(func.count(Repository.id)).where(Repository.user_id == user.id)
    )
    total = count_result.scalar() or 0

    # Fetch page
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user.id)
        .order_by(Repository.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    repos = result.scalars().all()

    return PaginatedRepoResponse(
        data=[RepositoryResponse.from_orm_repo(r) for r in repos],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


async def get_repository(repo_id: str, user: User, db: AsyncSession) -> RepositoryResponse:
    """Get a single repository by ID."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)
    log_repo_access(str(user.id), str(repo.id), "view")
    
    # Build file tree from code chunks if not in metadata
    meta = repo.metadata_jsonb or {}
    if not meta.get("file_tree") and repo.status == "completed":
        # Get all file paths from code chunks
        result = await db.execute(
            select(CodeChunk.file_path).where(CodeChunk.repo_id == repo.id).distinct()
        )
        file_paths = [row[0] for row in result.fetchall()]
        
        if file_paths:
            # Build tree structure from file paths
            file_tree = _build_tree_from_paths(file_paths)
            meta["file_tree"] = file_tree
            repo.metadata_jsonb = meta
            await db.flush()
    
    return RepositoryResponse.from_orm_repo(repo)


async def analyze_repository(
    github_url: str,
    user: User,
    db: AsyncSession,
) -> AnalyzeRepoResponse:
    """Start repository analysis — creates repo record and dispatches Celery task."""
    if not validate_github_url(github_url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    owner, repo_name = parse_github_url(github_url)

    # Get repo info from GitHub
    github_token = None
    if user.access_token_encrypted:
        try:
            github_token = decrypt_token(user.access_token_encrypted)
        except Exception:
            pass

    try:
        repo_info = await get_repo_info(owner, repo_name, github_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not access repository: {e}")

    # Check if already analyzed
    existing = await db.execute(
        select(Repository).where(
            Repository.user_id == user.id,
            Repository.github_url == github_url,
        )
    )
    existing_repo = existing.scalar_one_or_none()

    if existing_repo and existing_repo.status == "completed":
        return AnalyzeRepoResponse(
            repo_id=str(existing_repo.id),
            task_id="already-completed",
        )

    # Create or update repository record
    if existing_repo:
        repo = existing_repo
        repo.status = "pending"
        repo.processing_progress = 0.0
        repo.error_message = None
    else:
        repo = Repository(
            user_id=user.id,
            github_url=github_url,
            name=repo_info["name"],
            description=repo_info.get("description"),
            language=repo_info.get("language"),
            star_count=repo_info.get("star_count", 0),
            status="pending",
        )
        db.add(repo)

    await db.flush()

    # Dispatch Celery task
    task_id = str(uuid.uuid4())
    try:
        from app.tasks.repo_tasks import analyze_repo_task
        analyze_repo_task.delay(str(repo.id), str(user.id))
    except Exception as e:
        logger.warning("Celery not available, running sync: %s", e)
        # If Celery isn't running, mark as processing (would need manual trigger)
        repo.status = "processing"

    log_repo_access(str(user.id), str(repo.id), "analyze")

    return AnalyzeRepoResponse(repo_id=str(repo.id), task_id=task_id)


async def get_repository_status(repo_id: str, user: User, db: AsyncSession) -> RepoStatusResponse:
    """Get repository analysis status."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    return RepoStatusResponse(
        status=repo.status,
        progress=repo.processing_progress or 0.0,
        message=repo.error_message,
    )


async def get_repository_summary(repo_id: str, user: User, db: AsyncSession) -> RepositorySummaryResponse:
    """Get repository summary with cached results."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    meta = repo.metadata_jsonb or {}

    # If summary exists in metadata, use it
    if meta.get("summary"):
        summary_data = meta
    else:
        # Generate summary using AI
        summary_data = await generate_summary(str(repo.id), db)
        # Cache in metadata
        repo.metadata_jsonb = {**(repo.metadata_jsonb or {}), **summary_data}
        await db.flush()

    repo_response = RepositoryResponse.from_orm_repo(repo)

    return RepositorySummaryResponse(
        repository=repo_response,
        purpose=summary_data.get("purpose", ""),
        features=summary_data.get("features", []),
        tech_stack=summary_data.get("tech_stack", []),
        architecture=summary_data.get("architecture", ""),
        key_files=summary_data.get("key_files", []),
    )


async def regenerate_summary(repo_id: str, user: User, db: AsyncSession) -> RepositorySummaryResponse:
    """Force regenerate repository summary."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    summary_data = await generate_summary(str(repo.id), db)
    repo.metadata_jsonb = {**(repo.metadata_jsonb or {}), **summary_data}
    await db.flush()

    repo_response = RepositoryResponse.from_orm_repo(repo)

    return RepositorySummaryResponse(
        repository=repo_response,
        purpose=summary_data.get("purpose", ""),
        features=summary_data.get("features", []),
        tech_stack=summary_data.get("tech_stack", []),
        architecture=summary_data.get("architecture", ""),
        key_files=summary_data.get("key_files", []),
    )


async def delete_repository(repo_id: str, user: User, db: AsyncSession) -> dict:
    """Delete a repository and all related data."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)

    await db.delete(repo)
    log_repo_access(str(user.id), str(repo.id), "delete")

    return {"message": "Repository deleted successfully"}


async def get_file_content(repo_id: str, file_path: str, user: User, db: AsyncSession) -> dict:
    """Get the content of a specific file from the repository."""
    repo = await _get_repo_or_404(repo_id, db)
    check_repo_ownership(user, repo.user_id)
    
    # Get all chunks for this file path (in order)
    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id, CodeChunk.file_path == file_path)
        .order_by(CodeChunk.start_line)
    )
    chunks = result.scalars().all()
    
    if not chunks:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Combine content from all chunks
    content = "\n".join(chunk.content for chunk in chunks)
    
    return {
        "content": content,
        "file_path": file_path,
        "language": chunks[0].language if chunks else "text",
        "size": len(content),
    }


async def get_github_repos(user: User) -> list[GitHubRepoItem]:
    """List user's GitHub repositories."""
    if not user.access_token_encrypted:
        raise HTTPException(status_code=400, detail="No GitHub token available")

    github_token = decrypt_token(user.access_token_encrypted)
    repos = await list_user_repos(github_token)

    return [GitHubRepoItem(**r) for r in repos]


async def get_usage_quota(user: User, db: AsyncSession) -> UsageQuotaResponse:
    """Get user's usage quota stats."""
    # Count repos
    repo_count = await db.execute(
        select(func.count(Repository.id)).where(Repository.user_id == user.id)
    )
    repos_used = repo_count.scalar() or 0

    # Calculate storage (sum of code chunk content lengths)
    storage_result = await db.execute(
        select(func.sum(func.length(CodeChunk.content)))
        .join(Repository)
        .where(Repository.user_id == user.id)
    )
    storage_used = storage_result.scalar() or 0

    # TODO: Track chat requests per hour in Redis
    return UsageQuotaResponse(
        chat_requests={"used": 0, "limit": 50},
        repos_analyzed={"used": repos_used, "limit": 5},
        storage={"used": storage_used, "limit": 1_073_741_824},  # 1GB
        tier="free",
    )


# ── Helpers ──────────────────────────────────────────────
def _build_tree_from_paths(file_paths: list[str]) -> list[dict]:
    """Build a tree structure from a list of file paths."""
    root: dict[str, any] = {}
    
    for path in sorted(file_paths):
        parts = path.split('/')
        current = root
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # File
                if 'files' not in current:
                    current['files'] = []
                current['files'].append({
                    'id': path,
                    'path': path,
                    'name': part,
                    'type': 'file',
                    'language': _detect_language(part),
                })
            else:  # Directory
                if 'children' not in current:
                    current['children'] = {}
                if part not in current['children']:
                    current['children'][part] = {}
                current = current['children'][part]
    
    def _build_nodes(tree_dict: dict, prefix: str = '') -> list[dict]:
        nodes = []
        
        # Add directories
        if 'children' in tree_dict:
            for name, child in sorted(tree_dict['children'].items()):
                child_path = f"{prefix}/{name}" if prefix else name
                dir_node = {
                    'id': child_path,
                    'path': child_path,
                    'name': name,
                    'type': 'directory',
                    'children': _build_nodes(child, child_path),
                }
                nodes.append(dir_node)
        
        # Add files
        if 'files' in tree_dict:
            nodes.extend(tree_dict['files'])
        
        return nodes
    
    return _build_nodes(root)


def _detect_language(filename: str) -> str:
    """Detect language from file extension."""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    lang_map = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript',
        'jsx': 'jsx', 'tsx': 'tsx', 'java': 'java', 'rb': 'ruby',
        'go': 'go', 'rs': 'rust', 'php': 'php', 'c': 'c', 'cpp': 'cpp',
        'cs': 'csharp', 'swift': 'swift', 'kt': 'kotlin',
        'html': 'html', 'css': 'css', 'json': 'json', 'yaml': 'yaml',
        'md': 'markdown', 'sql': 'sql', 'sh': 'shell',
    }
    return lang_map.get(ext, 'text')


async def _get_repo_or_404(repo_id: str, db: AsyncSession) -> Repository:
    """Fetch a repository or raise 404."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


def _build_tree_from_paths(file_paths: list[str]) -> list[dict]:
    """Build a tree structure from flat file paths."""
    from collections import defaultdict
    
    tree = []
    # Group files by directory
    dir_map = defaultdict(list)
    
    for path in file_paths:
        parts = path.split("/")
        if len(parts) == 1:
            # Root level file
            tree.append({
                "id": path,
                "path": path,
                "name": path,
                "type": "file",
                "language": _detect_language_from_path(path),
            })
        else:
            # File in directory
            dir_path = "/".join(parts[:-1])
            dir_map[dir_path].append(path)
    
    # Build directory nodes
    processed_dirs = set()
    
    def add_directory(dir_path: str) -> dict:
        if dir_path in processed_dirs:
            return None
        processed_dirs.add(dir_path)
        
        parts = dir_path.split("/")
        name = parts[-1]
        
        children = []
        # Add files in this directory
        for file_path in dir_map.get(dir_path, []):
            file_name = file_path.split("/")[-1]
            children.append({
                "id": file_path,
                "path": file_path,
                "name": file_name,
                "type": "file",
                "language": _detect_language_from_path(file_path),
            })
        
        # Add subdirectories
        for other_dir in list(dir_map.keys()):
            if other_dir.startswith(dir_path + "/") and other_dir.count("/") == dir_path.count("/") + 1:
                subdir = add_directory(other_dir)
                if subdir:
                    children.append(subdir)
        
        return {
            "id": dir_path,
            "path": dir_path,
            "name": name,
            "type": "directory",
            "children": children,
        }
    
    # Add top-level directories
    for dir_path in sorted(dir_map.keys()):
        if "/" not in dir_path:  # Top-level directory
            dir_node = add_directory(dir_path)
            if dir_node:
                tree.append(dir_node)
    
    return tree


def _detect_language_from_path(file_path: str) -> str:
    """Detect language from file extension."""
    ext = file_path.split(".")[-1].lower()
    lang_map = {
        "py": "python", "js": "javascript", "ts": "typescript",
        "jsx": "jsx", "tsx": "tsx", "java": "java",
        "go": "go", "rs": "rust", "rb": "ruby",
        "php": "php", "c": "c", "cpp": "cpp",
        "cs": "csharp", "swift": "swift",
    }
    return lang_map.get(ext, "text")
