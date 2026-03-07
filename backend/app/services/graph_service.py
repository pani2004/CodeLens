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
    
    # Fetch all chunks for the repo
    result = await db.execute(
        select(CodeChunk).where(CodeChunk.repo_id == repo_id)
    )
    chunks = result.scalars().all()

    if not chunks:
        logger.warning(f"No chunks found for repo {repo_id}")
        return _empty_graph()

    logger.info(f"Processing {len(chunks)} code chunks")

    # Build directed graph
    G = nx.DiGraph()
    file_languages: dict[str, str] = {}
    file_sizes: dict[str, int] = {}

    # Add nodes (unique file paths)
    for chunk in chunks:
        fp = chunk.file_path
        if fp not in file_languages:
            file_languages[fp] = chunk.language or "text"
            file_sizes[fp] = 0
        file_sizes[fp] += len(chunk.content)

        if not G.has_node(fp):
            G.add_node(fp)

    logger.info(f"Graph has {G.number_of_nodes()} nodes")

    # Add edges (imports)
    for chunk in chunks:
        meta = chunk.metadata_jsonb or {}
        imports = meta.get("imports", [])
        for imp in imports:
            resolved = _resolve_import(imp, chunk.file_path, set(file_languages.keys()))
            if resolved and resolved != chunk.file_path:
                G.add_edge(chunk.file_path, resolved, type="import")

    logger.info(f"Graph has {G.number_of_edges()} edges")

    # Calculate metrics (simplified for large graphs)
    entry_points = [n for n in G.nodes() if G.in_degree(n) == 0]
    circular = []
    
    # Only calculate cycles if graph is not too large
    if G.number_of_nodes() < 500 and G.number_of_edges() > 0:
        try:
            circular = list(nx.simple_cycles(G))[:20]  # Limit to first 20
        except Exception as e:
            logger.warning(f"Could not calculate cycles: {e}")

    # Simplified centrality calculation for large graphs
    if G.number_of_nodes() < 200:
        try:
            betweenness = nx.betweenness_centrality(G)
        except Exception as e:
            logger.warning(f"Could not calculate betweenness: {e}")
            betweenness = {n: 0 for n in G.nodes()}
    else:
        # For large graphs, use simpler degree centrality
        logger.info("Using degree centrality for large graph")
        betweenness = {n: G.degree(n) / max(G.number_of_nodes() - 1, 1) for n in G.nodes()}

    # Build response
    nodes = []
    for i, fp in enumerate(G.nodes()):
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


def _resolve_import(import_path: str, source_file: str, known_files: set[str]) -> Optional[str]:
    """Attempt to resolve an import to a known file path."""
    # Normalize module path
    normalized = import_path.replace(".", "/")

    # Try common patterns
    candidates = [
        f"{normalized}.py",
        f"{normalized}/index.js",
        f"{normalized}/index.ts",
        f"{normalized}.js",
        f"{normalized}.ts",
        f"{normalized}.tsx",
        f"{normalized}.jsx",
        normalized,
    ]

    # Relative imports: resolve from source file's directory
    source_dir = "/".join(source_file.split("/")[:-1])
    if import_path.startswith("."):
        rel = import_path.lstrip("./").replace(".", "/")
        candidates = [
            f"{source_dir}/{rel}.py",
            f"{source_dir}/{rel}.js",
            f"{source_dir}/{rel}.jsx",
            f"{source_dir}/{rel}.ts",
            f"{source_dir}/{rel}.tsx",
            f"{source_dir}/{rel}/index.js",
            f"{source_dir}/{rel}/index.jsx",
            f"{source_dir}/{rel}/index.ts",
            f"{source_dir}/{rel}/index.tsx",
        ]

    for candidate in candidates:
        if candidate in known_files:
            return candidate

    return None


def _classify_node(file_path: str) -> str:
    """Classify a file node as file, module, or package."""
    if file_path.endswith("__init__.py") or file_path.endswith("index.js") or file_path.endswith("index.ts"):
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
