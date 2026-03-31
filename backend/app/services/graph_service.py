"""Dependency graph service — build import graphs using networkx."""

import re
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import networkx as nx

from app.models.code_chunk import CodeChunk

logger = logging.getLogger("codelens.graph")


async def build_dependency_graph(repo_id: str, db: AsyncSession) -> dict:
    """
    Build a dependency graph from code chunks.
    Nodes = files/modules, Edges = import relationships.
    Returns data matching frontend DependencyGraph interface.
    """
    logger.info(f"Building dependency graph for repo {repo_id}")

    result = await db.execute(
        select(CodeChunk).where(CodeChunk.repo_id == repo_id)
    )
    chunks = result.scalars().all()

    if not chunks:
        logger.warning(f"No chunks found for repo {repo_id}")
        return _empty_graph()

    logger.info(f"Processing {len(chunks)} code chunks")

    G = nx.DiGraph()
    file_languages: dict[str, str] = {}
    file_sizes: dict[str, int] = {}

    # Add nodes
    for chunk in chunks:
        fp = chunk.file_path
        if fp not in file_languages:
            file_languages[fp] = chunk.language or "text"
            file_sizes[fp] = 0
        file_sizes[fp] += len(chunk.content)
        if not G.has_node(fp):
            G.add_node(fp)

    known_files = set(file_languages.keys())
    logger.info(f"Graph has {G.number_of_nodes()} nodes")

    # Add edges
    edges_added = 0
    edges_attempted = 0

    for chunk in chunks:
        meta = chunk.metadata_jsonb or {}

        imports = meta.get("imports", [])
        if not imports:
            imports = _extract_imports_from_content(chunk.content, chunk.language or "")

        for imp in imports:
            edges_attempted += 1
            resolved = _resolve_import(imp, chunk.file_path, known_files)
            if resolved and resolved != chunk.file_path:
                if not G.has_edge(chunk.file_path, resolved):
                    G.add_edge(chunk.file_path, resolved, type="import")
                    edges_added += 1

    logger.info(f"Edges attempted: {edges_attempted}, added: {edges_added}")
    logger.info(f"Graph has {G.number_of_edges()} edges")

    entry_points = [n for n in G.nodes() if G.in_degree(n) == 0]
    circular = []

    if G.number_of_nodes() < 500 and G.number_of_edges() > 0:
        try:
            circular = list(nx.simple_cycles(G))[:20]
        except Exception as e:
            logger.warning(f"Could not calculate cycles: {e}")

    if G.number_of_nodes() < 200:
        try:
            betweenness = nx.betweenness_centrality(G)
        except Exception as e:
            logger.warning(f"Could not calculate betweenness: {e}")
            betweenness = {n: 0 for n in G.nodes()}
    else:
        betweenness = {n: G.degree(n) / max(G.number_of_nodes() - 1, 1) for n in G.nodes()}

    nodes = []
    for fp in G.nodes():
        node_type = _classify_node(fp)
        nodes.append({
            "id": fp,
            "label": fp.split("/")[-1],
            "type": node_type,
            "language": file_languages.get(fp, "text"),
            "size": file_sizes.get(fp, 0),
            "complexity": int(betweenness.get(fp, 0) * 100),
        })

    edges = []
    for src, tgt, data in G.edges(data=True):
        edges.append({
            "source": src,
            "target": tgt,
            "type": data.get("type", "import"),
            "weight": 1,
        })

    logger.info(f"Graph build complete: {len(nodes)} nodes, {len(edges)} edges")

    return {
        "nodes": nodes,
        "edges": edges,
        "entry_points": entry_points[:10],
        "metrics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "circular_dependencies": [list(c) for c in circular],
        },
    }


def _extract_imports_from_content(content: str, language: str) -> list[str]:
    """
     Fallback: parse imports directly from file content.
    Handles JS/TS/Python/Angular patterns.
    """
    imports = []
    if not content:
        return imports

    # JS/TS: import ... from '...' or require('...')
    if language in ("javascript", "typescript", "js", "ts", "jsx", "tsx", ""):
        # import X from 'path'
        # import { X } from 'path'
        # import 'path'
        for match in re.finditer(
            r"""import\s+(?:[\w*{}\s,]+\s+from\s+)?['"]([^'"]+)['"]""",
            content
        ):
            imports.append(match.group(1))

        # require('path')
        for match in re.finditer(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", content):
            imports.append(match.group(1))

    # Python: import X / from X import Y
    if language in ("python", "py"):
        for match in re.finditer(r"""^from\s+([\w.]+)\s+import""", content, re.MULTILINE):
            imports.append(match.group(1))
        for match in re.finditer(r"""^import\s+([\w.]+)""", content, re.MULTILINE):
            imports.append(match.group(1))

    return imports


def _resolve_import(import_path: str, source_file: str, known_files: set[str]) -> Optional[str]:
    """
   
    """
    # Skip node_modules and external packages
    if _is_external_package(import_path):
        return None

    source_dir = "/".join(source_file.split("/")[:-1])

    # properly handle relative imports including ../
    if import_path.startswith("."):
        resolved_dir = _resolve_relative_dir(source_dir, import_path)
        # Strip the trailing filename part
        base = import_path.split("/")[-1]
        # Remove leading dots
        base = re.sub(r'^\.+/', '', import_path)
        base = base.split("/")[-1]

        candidates = [
            f"{resolved_dir}/{base}.ts",
            f"{resolved_dir}/{base}.tsx",
            f"{resolved_dir}/{base}.js",
            f"{resolved_dir}/{base}.jsx",
            f"{resolved_dir}/{base}.py",
            f"{resolved_dir}/{base}/index.ts",
            f"{resolved_dir}/{base}/index.tsx",
            f"{resolved_dir}/{base}/index.js",
            f"{resolved_dir}/{base}/index.jsx",
            f"{resolved_dir}/{base}",
        ]
    else:
        # absolute imports — try matching against known file suffixes
        # e.g. '@app/services/auth' → look for any known file ending in 'services/auth.ts' etc.
        normalized = import_path.lstrip("@").replace("@", "/")
        # Remove common aliases like 'app/', 'src/'
        path_variants = [
            normalized,
            "/".join(normalized.split("/")[1:]),  # strip first segment (alias)
        ]

        candidates = []
        for variant in path_variants:
            if not variant:
                continue
            candidates += [
                f"{variant}.ts",
                f"{variant}.tsx",
                f"{variant}.js",
                f"{variant}.jsx",
                f"{variant}.py",
                f"{variant}/index.ts",
                f"{variant}/index.js",
                f"src/{variant}.ts",
                f"src/{variant}.tsx",
                f"src/{variant}.js",
                f"src/{variant}/index.ts",
                f"client/{variant}.ts",
                f"client/{variant}.tsx",
                f"client/{variant}.js",
                f"client/{variant}/index.ts",
            ]

        # fuzzy suffix match against known files
        for known in known_files:
            for variant in path_variants:
                if variant and known.endswith(variant + ".ts") or known.endswith(variant + ".js"):
                    candidates.append(known)

    for candidate in candidates:
        # Normalize double slashes
        candidate = re.sub(r'/+', '/', candidate)
        if candidate in known_files:
            return candidate

    return None


def _resolve_relative_dir(source_dir: str, import_path: str) -> str:
    """

    e.g. source_dir='src/app/components', import='../services/auth'
    → 'src/app/services'
    """
    parts = source_dir.split("/") if source_dir else []

    # Count how many levels up we need to go
    segments = import_path.split("/")
    for seg in segments[:-1]:  # all but the last (filename) part
        if seg == "..":
            if parts:
                parts.pop()
        elif seg == ".":
            pass  # stay in same dir
        else:
            parts.append(seg)

    return "/".join(parts)


def _is_external_package(import_path: str) -> bool:
    """
    Filter out node_modules and Python stdlib/third-party imports.
    """
    # Relative imports are always local
    if import_path.startswith("."):
        return False

    # Angular/common scoped packages
    external_scopes = (
        "@angular/", "@ngrx/", "@ngx-", "rxjs", "rxjs/",
        "zone.js", "tslib", "lodash", "axios", "express",
        "react", "react-dom", "next", "vue",
        "os", "sys", "re", "json", "math", "io",
        "collections", "typing", "pathlib", "datetime",
        "flask", "django", "fastapi", "sqlalchemy",
    )
    for scope in external_scopes:
        if import_path.startswith(scope) or import_path == scope.rstrip("/"):
            return True

    # Pure package names (no slashes, no dots) are likely external
    if "/" not in import_path and "." not in import_path:
        return True

    return False


def _classify_node(file_path: str) -> str:
    """Classify a file node as file, module, or package."""
    name = file_path.split("/")[-1]
    if name in ("__init__.py", "index.js", "index.ts", "index.jsx", "index.tsx"):
        return "package"
    if "/" in file_path:
        return "module"
    return "file"


def _empty_graph() -> dict:
    return {
        "nodes": [],
        "edges": [],
        "entry_points": [],
        "metrics": {
            "total_nodes": 0,
            "total_edges": 0,
            "circular_dependencies": [],
        },
    }