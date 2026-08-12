"""Seed and verify the live Neo4j graph used by the MCP generation workflow."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.graph_store import Neo4jCatalog  # noqa: E402
from graph_mcp.workflow import (  # noqa: E402
    REQUIRED_SYMBOLS,
    GenerationWorkflow,
    GraphCatalog,
)

COUNT_QUERY = """
MATCH (fixture:Fixture {fixtureId: $fixture_id})-[:CONTAINS]->(symbol:Symbol)
OPTIONAL MATCH (symbol)-[:DEFINES]->(method:Method)
RETURN count(DISTINCT symbol) AS symbol_count,
       count(DISTINCT method) AS method_count
"""

REQUEST = (
    "Create LiveGraphWorkflow as a Java test workflow in generated.tests "
    "backed by module live_graph and config testtables/LiveGraph.toml for v1.0.0."
)


def verify() -> dict:
    fixture = GraphCatalog.from_path(ROOT / "fixtures" / "synthetic_graph.json")
    store = Neo4jCatalog.from_env()
    try:
        seed_report = store.seed(fixture)
        server_info = store.driver.get_server_info()
        retrieved = [store.get(name, fixture.version).name for name in REQUIRED_SYMBOLS]
        search_matches = store.search("defineTestSequences", fixture.version)
        workflow_result = GenerationWorkflow(store).run_text(REQUEST)
        with store.driver.session() as session:
            counts = session.run(
                COUNT_QUERY,
                fixture_id=fixture.fixture_id,
            ).single(strict=True)
    finally:
        store.close()

    if workflow_result["status"] != "generated":
        raise RuntimeError("Live Neo4j-backed generation did not pass validation")
    if set(retrieved) != set(REQUIRED_SYMBOLS):
        raise RuntimeError("Live graph did not return every required symbol")

    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "server_agent": server_info.agent,
        "protocol_version": str(server_info.protocol_version),
        "fixture_id": seed_report["fixture_id"],
        "fixture_sha256": seed_report["fixture_hash"],
        "fixture_version": seed_report["version"],
        "symbol_count": counts["symbol_count"],
        "method_count": counts["method_count"],
        "required_symbol_count": len(retrieved),
        "method_search_match_count": len(search_matches),
        "generation_status": workflow_result["status"],
        "generation_groundedness": workflow_result["validation"]["groundedness"],
        "generation_validation_passed": workflow_result["validation"]["valid"],
        "credentials_recorded": False,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "scope": "temporary local Neo4j Community instance",
        },
        "command": "python scripts/verify_neo4j.py",
    }


def main() -> int:
    result = verify()
    output = ROOT / "evidence" / "neo4j_integration.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
