import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.graph_store import Neo4jCatalog  # noqa: E402
from graph_mcp.workflow import GraphCatalog  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_NEO4J_INTEGRATION") != "1",
    reason="Set RUN_NEO4J_INTEGRATION=1 for the live Neo4j gate",
)


def test_live_neo4j_seed_and_grounded_lookup():
    fixture = GraphCatalog.from_path(ROOT / "fixtures" / "synthetic_graph.json")
    store = Neo4jCatalog.from_env()
    try:
        report = store.seed(fixture)
        match = store.get("ConfigLoader", "v1.0.0")
        search = store.search("defineTestSequences", "v1.0.0")
    finally:
        store.close()

    assert report["symbol_count"] == 8
    assert match.qualified_name == "synthetic.framework.config.ConfigLoader"
    assert any(item["name"] == "BaseTestMethod" for item in search)
