"""Materialize the independently generated synthetic catalog in Neo4j."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.graph_store import Neo4jCatalog  # noqa: E402
from graph_mcp.workflow import GraphCatalog  # noqa: E402


def main() -> int:
    catalog = GraphCatalog.from_path(ROOT / "fixtures" / "synthetic_graph.json")
    store = Neo4jCatalog.from_env()
    try:
        print(json.dumps(store.seed(catalog), indent=2))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
