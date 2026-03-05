"""Input validation helpers."""

import re
from pathlib import PurePosixPath
from typing import Optional


GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+/?$"
)


def validate_github_url(url: str) -> bool:
    """Check if a string is a valid GitHub repository URL."""
    return bool(GITHUB_URL_PATTERN.match(url.strip()))


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL."""
    url = url.strip().rstrip("/")
    parts = url.split("/")
    if len(parts) < 5:
        raise ValueError(f"Invalid GitHub URL: {url}")
    owner = parts[-2]
    repo = parts[-1].replace(".git", "")
    return owner, repo


def sanitize_file_path(path: str) -> str:
    """Sanitize file path to prevent path traversal attacks."""
    # Normalize separators
    path = path.replace("\\", "/")

    # Block path traversal
    if ".." in path.split("/"):
        raise ValueError("Path traversal detected")

    # Remove leading slashes
    path = path.lstrip("/")

    # Validate with PurePosixPath
    clean = str(PurePosixPath(path))
    if clean.startswith("/") or ".." in clean:
        raise ValueError("Invalid file path")

    return clean


def validate_chunk_type(chunk_type: str) -> bool:
    return chunk_type in ("file", "class", "function", "block")


def validate_repo_status(status: str) -> bool:
    return status in ("pending", "processing", "completed", "failed")
