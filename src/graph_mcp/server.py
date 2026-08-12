"""Official MCP stdio server for the bounded synthetic generation workflow."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .graph_store import Neo4jCatalog
from .workflow import (
    REQUIRED_SYMBOLS,
    GenerationIntent,
    GenerationWorkflow,
    GraphCatalog,
    JavaValidator,
    WorkflowRejection,
)

ROOT = Path(__file__).resolve().parents[2]


def _fixture_path() -> Path:
    configured = os.getenv("GRAPH_FIXTURE_PATH")
    candidates = [
        Path(configured) if configured else None,
        Path.cwd() / "fixtures" / "synthetic_graph.json",
        ROOT / "fixtures" / "synthetic_graph.json",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("Set GRAPH_FIXTURE_PATH to the synthetic graph fixture")


CATALOG_PATH = _fixture_path()
GRAPH_BACKEND = os.getenv("GRAPH_BACKEND", "fixture").casefold()
if GRAPH_BACKEND == "fixture":
    CATALOG = GraphCatalog.from_path(CATALOG_PATH)
elif GRAPH_BACKEND == "neo4j":
    CATALOG = Neo4jCatalog.from_env()
else:
    raise RuntimeError("GRAPH_BACKEND must be either 'fixture' or 'neo4j'")
WORKFLOW = GenerationWorkflow(CATALOG)

mcp = FastMCP(
    name="synthetic-java-test-generator",
    instructions=(
        "Retrieve synthetic framework context before generating Java. "
        "Generation fails closed on invalid identifiers, unsafe paths, missing "
        "graph context, syntax errors, ungrounded imports, or forbidden APIs."
    ),
    log_level="WARNING",
)


@mcp.tool()
def get_fixture_metadata() -> dict[str, Any]:
    """Return provenance and version information for the active graph fixture."""
    return {
        "fixture_id": CATALOG.fixture_id,
        "version": CATALOG.version,
        "provenance": CATALOG.provenance,
        "license": CATALOG.license,
        "backend": GRAPH_BACKEND,
        "symbol_count": len(CATALOG.search("synthetic.framework", CATALOG.version, 20)),
    }


@mcp.tool()
def search_graph(query: str, version: str = "v1.0.0", limit: int = 8) -> dict[str, Any]:
    """Search the bounded synthetic graph by class, qualified name, or method."""
    try:
        return {
            "status": "ok",
            "matches": CATALOG.search(query, version, limit),
            "fixture_id": CATALOG.fixture_id,
        }
    except WorkflowRejection as exc:
        return {
            "status": "rejected",
            "matches": [],
            "error": {"code": exc.code, "message": str(exc)},
        }


@mcp.tool()
def generate_java_test(
    class_name: str,
    package_name: str,
    module_name: str,
    config_path: str,
    version: str = "v1.0.0",
) -> dict[str, Any]:
    """Generate Java only when graph grounding, syntax, contract, and safety pass."""
    return WORKFLOW.run(
        {
            "class_name": class_name,
            "package_name": package_name,
            "module_name": module_name,
            "config_path": config_path,
            "version": version,
        }
    )


@mcp.tool()
def generate_java_test_from_intent(request: str) -> dict[str, Any]:
    """Parse a bounded natural-language request, generate Java, and enforce all gates."""
    return WORKFLOW.run_text(request)


@mcp.tool()
def validate_java_source(
    source: str,
    class_name: str,
    package_name: str,
    module_name: str,
    config_path: str,
    version: str = "v1.0.0",
) -> dict[str, Any]:
    """Validate bounded Java source against syntax, graph, contract, and safety gates."""
    if len(source) > 20_000 or "\x00" in source:
        return {
            "status": "rejected",
            "error": {
                "code": "invalid_source_size",
                "message": "Source must be non-binary and no larger than 20,000 characters",
            },
        }
    try:
        intent = GenerationIntent.from_mapping(
            {
                "class_name": class_name,
                "package_name": package_name,
                "module_name": module_name,
                "config_path": config_path,
                "version": version,
            }
        )
        citations = tuple(CATALOG.get(name, version) for name in REQUIRED_SYMBOLS)
        report = JavaValidator().validate(source, intent, citations)
        return {"status": "valid" if report.valid else "invalid", "validation": asdict(report)}
    except WorkflowRejection as exc:
        return {
            "status": "rejected",
            "error": {"code": exc.code, "message": str(exc)},
        }


def main() -> None:
    """Start the server using MCP's stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
