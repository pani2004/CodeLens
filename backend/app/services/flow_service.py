"""Execution flow tracing service — detect routes, trace call graphs, generate flow data."""

import re
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.code_chunk import CodeChunk

logger = logging.getLogger("codelens.flow")

# ── Framework detection patterns ─────────────────────────
FRAMEWORK_PATTERNS = {
    "fastapi": [
        r"@(?:app|router)\.(get|post|put|delete|patch)\(",
        r"from\s+fastapi\s+import",
        r"FastAPI\(\)",
    ],
    "flask": [
        r"@(?:app|blueprint)\.(route|get|post|put|delete)\(",
        r"from\s+flask\s+import",
        r"Flask\(__name__\)",
    ],
    "express": [
        r"(?:app|router)\.(get|post|put|delete|patch|use)\(",
        r"require\(['\"]express['\"]\)",
        r"import\s+express\s+from",
    ],
    "django": [
        r"urlpatterns\s*=",
        r"from\s+django",
        r"class\s+\w+View\(",
    ],
    "nextjs": [
        r"export\s+(?:default\s+)?(?:async\s+)?function\s+(?:GET|POST|PUT|DELETE|PATCH)",
        r"from\s+['\"]next",
        r"NextResponse",
    ],
}


async def detect_framework(repo_id: str, db: AsyncSession) -> Optional[str]:
    """Detect the web framework used in the repository."""
    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .limit(100)
    )
    chunks = result.scalars().all()
    combined_content = "\n".join(c.content for c in chunks)

    scores: dict[str, int] = {}
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        score = sum(
            len(re.findall(pattern, combined_content))
            for pattern in patterns
        )
        if score > 0:
            scores[framework] = score

    if not scores:
        return None

    return max(scores, key=scores.get)


async def get_execution_flows(repo_id: str, db: AsyncSession) -> list[dict]:
    """
    Extract execution flows (API routes/endpoints) from the codebase.
    Returns data matching frontend ExecutionFlow interface.
    """
    framework = await detect_framework(repo_id, db)
    if not framework:
        return []

    result = await db.execute(
        select(CodeChunk).where(CodeChunk.repo_id == repo_id)
    )
    chunks = result.scalars().all()

    flows = []

    for chunk in chunks:
        routes = _extract_routes(chunk.content, chunk.file_path, framework, chunk.start_line)
        flows.extend(routes)

    # Generate nodes and edges for each flow
    for i, flow in enumerate(flows):
        flow["id"] = f"flow-{i}"
        flow["nodes"], flow["edges"] = _generate_flow_diagram(flow)
        flow["complexity"] = len(flow.get("steps", []))

    return flows


def _extract_routes(content: str, file_path: str, framework: str, base_line: int) -> list[dict]:
    """Extract route definitions from code content."""
    routes = []
    lines = content.split("\n")

    if framework in ("fastapi", "flask"):
        pattern = r"@(?:app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"](.*?)\)"
        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                method = match.group(1).upper()
                route = match.group(2)

                # Find the handler function
                handler_name = ""
                for j in range(i + 1, min(i + 5, len(lines))):
                    func_match = re.match(r"\s*(?:async\s+)?def\s+(\w+)", lines[j])
                    if func_match:
                        handler_name = func_match.group(1)
                        break

                steps = _trace_handler_steps(lines, i, file_path, base_line, framework)

                routes.append({
                    "route": route,
                    "method": method,
                    "description": f"{method} {route} → {handler_name}()",
                    "steps": steps,
                })

    elif framework == "express":
        pattern = r"(?:app|router)\.(get|post|put|delete|patch|use)\(['\"]([^'\"]+)['\"]"
        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                method = match.group(1).upper()
                route = match.group(2)

                steps = _trace_handler_steps(lines, i, file_path, base_line, framework)

                routes.append({
                    "route": route,
                    "method": method if method != "USE" else "MIDDLEWARE",
                    "description": f"{method} {route}",
                    "steps": steps,
                })

    elif framework == "nextjs":
        pattern = r"export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)"
        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                method = match.group(1)
                # Derive route from file path e.g. app/api/users/route.ts → /api/users
                route = _file_path_to_route(file_path)

                steps = _trace_handler_steps(lines, i, file_path, base_line, framework)

                routes.append({
                    "route": route,
                    "method": method,
                    "description": f"{method} {route}",
                    "steps": steps,
                })

    return routes


def _trace_handler_steps(lines: list[str], start_idx: int, file_path: str, base_line: int, framework: str) -> list[dict]:
    """Trace execution steps within a route handler."""
    steps = []
    order = 1

    # Step 1: Entry point
    steps.append({
        "order": order,
        "type": "handler",
        "file_path": file_path,
        "function_name": "route_handler",
        "line_number": base_line + start_idx,
        "description": "Request received",
    })
    order += 1

    # Scan the handler body for patterns
    brace_count = 0
    in_handler = False

    for j in range(start_idx, min(start_idx + 100, len(lines))):
        line = lines[j].strip()

        # Track function scope
        brace_count += line.count("{") + line.count(":") - line.count("}")
        if "def " in line or "function " in line or "=>" in line:
            in_handler = True

        if not in_handler and j > start_idx:
            continue

        # Detect middleware calls
        if re.search(r"Depends\(|middleware|auth|verify|validate", line, re.IGNORECASE):
            steps.append({
                "order": order,
                "type": "middleware",
                "file_path": file_path,
                "function_name": _extract_call_name(line),
                "line_number": base_line + j,
                "description": "Authentication/validation check",
            })
            order += 1

        # Detect database operations
        elif re.search(r"\.query|\.execute|\.find|\.create|\.update|\.delete|session\.|db\.", line, re.IGNORECASE):
            steps.append({
                "order": order,
                "type": "database",
                "file_path": file_path,
                "function_name": _extract_call_name(line),
                "line_number": base_line + j,
                "description": "Database operation",
            })
            order += 1

        # Detect external API calls
        elif re.search(r"httpx\.|requests\.|fetch\(|axios\.", line, re.IGNORECASE):
            steps.append({
                "order": order,
                "type": "external_api",
                "file_path": file_path,
                "function_name": _extract_call_name(line),
                "line_number": base_line + j,
                "description": "External API call",
            })
            order += 1

        # Detect response
        elif re.search(r"return|Response|JSONResponse|jsonify|res\.(json|send|status)", line, re.IGNORECASE):
            steps.append({
                "order": order,
                "type": "response",
                "file_path": file_path,
                "function_name": "send_response",
                "line_number": base_line + j,
                "description": "Send response",
            })
            order += 1
            break

    return steps


def _extract_call_name(line: str) -> str:
    """Extract function/method name from a line of code."""
    match = re.search(r"(\w+)\s*\(", line)
    return match.group(1) if match else "unknown"


def _file_path_to_route(file_path: str) -> str:
    """Convert Next.js file path to route, e.g. app/api/users/route.ts → /api/users."""
    route = file_path.replace("\\", "/")
    route = re.sub(r"^(src/)?app", "", route)
    route = re.sub(r"/route\.(ts|js|tsx|jsx)$", "", route)
    route = re.sub(r"/page\.(ts|js|tsx|jsx)$", "", route)
    return route or "/"


def _generate_flow_diagram(flow: dict) -> tuple[list[dict], list[dict]]:
    """Generate nodes and edges for React Flow visualization."""
    steps = flow.get("steps", [])
    if not steps:
        return [], []

    nodes = []
    edges = []

    # Start node
    nodes.append({
        "id": "start",
        "type": "start",
        "label": f"{flow['method']} {flow['route']}",
        "description": "Incoming request",
    })

    prev_id = "start"
    for step in steps:
        node_id = f"step-{step['order']}"
        nodes.append({
            "id": node_id,
            "type": _step_type_to_node_type(step["type"]),
            "label": step["function_name"],
            "description": step["description"],
        })
        edges.append({
            "source": prev_id,
            "target": node_id,
            "label": step["type"],
        })
        prev_id = node_id

    # End node
    nodes.append({
        "id": "end",
        "type": "end",
        "label": "Response",
        "description": "Response sent to client",
    })
    edges.append({
        "source": prev_id,
        "target": "end",
    })

    return nodes, edges


def _step_type_to_node_type(step_type: str) -> str:
    """Map step type to React Flow node type."""
    mapping = {
        "middleware": "decision",
        "handler": "process",
        "database": "process",
        "external_api": "process",
        "response": "end",
    }
    return mapping.get(step_type, "process")
