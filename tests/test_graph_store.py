import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.graph_store import SEARCH_SYMBOLS_QUERY, Neo4jCatalog  # noqa: E402


class _Rows:
    def __iter__(self):
        return iter(
            [
                {
                    "name": "ConfigLoader",
                    "qualified_name": "synthetic.framework.config.ConfigLoader",
                    "kind": "class",
                    "methods": ["load"],
                }
            ]
        )


class _Session:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def run(self, cypher, **parameters):
        self.calls.append((cypher, parameters))
        return _Rows()


class _Driver:
    def __init__(self):
        self.active_session = _Session()

    def session(self):
        return self.active_session

    def close(self):
        return None


def test_uri_rejects_embedded_credentials_and_non_neo4j_schemes():
    with pytest.raises(ValueError, match="must not embed credentials"):
        Neo4jCatalog.validate_uri("bolt://user:password@localhost:7687")
    with pytest.raises(ValueError, match="allowed Neo4j scheme"):
        Neo4jCatalog.validate_uri("https://localhost:7687")


def test_search_uses_parameters_instead_of_interpolating_input():
    driver = _Driver()
    catalog = Neo4jCatalog(driver)
    hostile_query = "ConfigLoader') MATCH (n) DETACH DELETE n //"

    rows = catalog.search(hostile_query, "v1.0.0")

    executed_query, parameters = driver.active_session.calls[0]
    assert rows[0]["name"] == "ConfigLoader"
    assert executed_query == SEARCH_SYMBOLS_QUERY
    assert hostile_query not in executed_query
    assert parameters["search_text"] == hostile_query
    assert parameters["limit"] == 8


def test_from_env_requires_all_credentials(monkeypatch):
    for name in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="NEO4J_PASSWORD"):
        Neo4jCatalog.from_env(driver=_Driver())
