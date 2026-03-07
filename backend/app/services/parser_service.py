"""Code parsing service — clone repos, detect languages, parse into chunks."""

import ast
import os
import tarfile
import tempfile
import shutil
import io
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.utils.validators import sanitize_file_path

settings = get_settings()

# ── File filters ─────────────────────────────────────────
IGNORE_DIRS = {
    "node_modules", ".git", ".svn", "__pycache__", ".next", ".nuxt",
    "dist", "build", ".cache", "coverage", ".tox", ".mypy_cache",
    ".pytest_cache", "venv", "env", ".venv", ".env", "vendor",
    "target", "out", "bin", "obj", ".idea", ".vscode",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift",
    ".kt", ".scala", ".vue", ".svelte", ".sql", ".sh", ".bash",
    ".yaml", ".yml", ".json", ".toml", ".md", ".txt", ".html",
    ".css", ".scss", ".less",
}

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "jsx", ".tsx": "tsx", ".java": "java", ".go": "go",
    ".rs": "rust", ".rb": "ruby", ".php": "php", ".c": "c",
    ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
    ".vue": "vue", ".svelte": "svelte", ".sql": "sql",
    ".sh": "shell", ".bash": "shell", ".yaml": "yaml",
    ".yml": "yaml", ".json": "json", ".toml": "toml",
    ".md": "markdown", ".html": "html", ".css": "css",
    ".scss": "scss", ".less": "less",
}


# ── Repository cloning ──────────────────────────────────
def extract_tarball(tarball_bytes: bytes, dest_dir: str) -> str:
    """Extract a GitHub tarball to a directory. Returns the repo root path."""
    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        # GitHub tarballs have a top-level directory like owner-repo-sha/
        members = tar.getmembers()
        top_dir = members[0].name.split("/")[0] if members else ""
        tar.extractall(dest_dir)

    repo_root = os.path.join(dest_dir, top_dir) if top_dir else dest_dir
    return repo_root


# ── File filtering ───────────────────────────────────────
def should_include_file(file_path: str) -> bool:
    """Check if a file should be included in analysis."""
    path = Path(file_path)

    # Check ignored directories
    for part in path.parts:
        if part in IGNORE_DIRS:
            return False

    # Check ignored filenames
    if path.name in IGNORE_FILES:
        return False

    # Check extension
    if path.suffix.lower() not in CODE_EXTENSIONS:
        return False

    return True


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext, "text")


def get_repo_files(repo_path: str) -> list[dict]:
    """Walk repo directory and return list of includable files."""
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        # Skip ignored directories in-place for efficiency
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for name in filenames:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, repo_path).replace("\\", "/")

            if should_include_file(rel_path):
                try:
                    size = os.path.getsize(full_path)
                    if size > 1_000_000:  # Skip files > 1MB
                        continue
                    files.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "language": detect_language(rel_path),
                        "size": size,
                    })
                except OSError:
                    continue

    return files


# ── Python AST parsing ───────────────────────────────────
def parse_python_file(content: str, file_path: str) -> list[dict]:
    """Parse Python file using ast to extract classes and functions."""
    chunks = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    lines = content.split("\n")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno or start
            chunk_content = "\n".join(lines[start - 1:end])
            chunks.append({
                "file_path": file_path,
                "chunk_type": "class",
                "content": chunk_content,
                "start_line": start,
                "end_line": end,
                "metadata": {
                    "symbols": [node.name],
                    "imports": [],
                    "exports": [],
                },
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip methods inside classes (they'll be part of class chunk)
            start = node.lineno
            end = node.end_lineno or start
            chunk_content = "\n".join(lines[start - 1:end])
            chunks.append({
                "file_path": file_path,
                "chunk_type": "function",
                "content": chunk_content,
                "start_line": start,
                "end_line": end,
                "metadata": {
                    "symbols": [node.name],
                    "imports": [],
                    "exports": [],
                },
            })

    return chunks


# ── Generic JS/TS parsing (regex-based fallback) ────────
def parse_js_ts_file(content: str, file_path: str) -> list[dict]:
    """Parse JS/TS file using simple heuristics to extract functions/classes."""
    import re
    chunks = []
    lines = content.split("\n")

    # Match function/class declarations
    patterns = [
        (r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)", "function"),
        (r"^(?:export\s+)?(?:default\s+)?class\s+(\w+)", "class"),
        (r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(", "function"),
        (r"^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>|function)", "function"),
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()
        for pattern, chunk_type in patterns:
            match = re.match(pattern, stripped)
            if match:
                name = match.group(1)
                start_line = i + 1
                # Find end of block by counting braces
                brace_count = 0
                end_line = start_line
                for j in range(i, len(lines)):
                    brace_count += lines[j].count("{") - lines[j].count("}")
                    if brace_count <= 0 and j > i:
                        end_line = j + 1
                        break
                else:
                    end_line = len(lines)

                chunk_content = "\n".join(lines[start_line - 1:end_line])
                chunks.append({
                    "file_path": file_path,
                    "chunk_type": chunk_type,
                    "content": chunk_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "metadata": {
                        "symbols": [name],
                        "imports": [],
                        "exports": [],
                    },
                })
                break

    return chunks


# ── Hybrid chunking strategy ────────────────────────────
def chunk_file(content: str, file_path: str, language: str) -> list[dict]:
    """
    Hybrid chunking:
    - Files < 100 LOC → single file-level chunk
    - Files ≥ 100 LOC → function/class-level chunks
    - Falls back to file-level if parsing yields nothing
    """
    lines = content.split("\n")
    line_count = len(lines)
    
    # Extract imports once for the entire file
    file_imports = _extract_imports(content, language)

    # Small files: return as single chunk
    if line_count < 100:
        return [{
            "file_path": file_path,
            "chunk_type": "file",
            "content": content,
            "language": language,
            "start_line": 1,
            "end_line": line_count,
            "metadata": {
                "symbols": [],
                "imports": file_imports,
                "exports": [],
            },
        }]

    # Larger files: parse into function/class chunks
    chunks = []
    if language == "python":
        chunks = parse_python_file(content, file_path)
    elif language in ("javascript", "typescript", "jsx", "tsx"):
        chunks = parse_js_ts_file(content, file_path)

    # Add language to all chunks and file-level imports
    for chunk in chunks:
        chunk["language"] = language
        # Add file-level imports to each chunk's metadata
        chunk["metadata"]["imports"] = file_imports

    # Fallback: if no chunks, use file-level chunking
    if not chunks:
        return [{
            "file_path": file_path,
            "chunk_type": "file",
            "content": content,
            "language": language,
            "start_line": 1,
            "end_line": line_count,
            "metadata": {
                "symbols": [],
                "imports": file_imports,
                "exports": [],
            },
        }]

    return chunks


def _extract_imports(content: str, language: str) -> list[str]:
    """Extract import statements from source code."""
    import re
    imports = []

    if language == "python":
        for match in re.finditer(r"^(?:from\s+(\S+)\s+)?import\s+(.+)$", content, re.MULTILINE):
            module = match.group(1) or match.group(2).split(",")[0].strip().split(" ")[0]
            imports.append(module)
    elif language in ("javascript", "typescript", "jsx", "tsx"):
        for match in re.finditer(r"(?:import\s+.+\s+from\s+['\"](.+?)['\"]|require\(['\"](.+?)['\"]\))", content):
            imports.append(match.group(1) or match.group(2))

    return imports


# ── File tree builder ────────────────────────────────────
def build_file_tree(repo_path: str) -> list[dict]:
    """Build a tree structure of the repository for the file explorer."""
    def _build(path: str, rel_base: str) -> list[dict]:
        items = []
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return items

        # Directories first, then files
        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in IGNORE_DIRS]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]

        for d in dirs:
            full = os.path.join(path, d)
            rel = f"{rel_base}/{d}" if rel_base else d
            children = _build(full, rel)
            if children:  # Only include non-empty dirs
                items.append({
                    "id": rel,
                    "path": rel,
                    "name": d,
                    "type": "directory",
                    "children": children,
                })

        for f in files:
            rel = f"{rel_base}/{f}" if rel_base else f
            full = os.path.join(path, f)
            if should_include_file(rel):
                items.append({
                    "id": rel,
                    "path": rel,
                    "name": f,
                    "type": "file",
                    "language": detect_language(f),
                    "size": os.path.getsize(full),
                })

        return items

    return _build(repo_path, "")
