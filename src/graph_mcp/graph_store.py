"""Parameterized Neo4j adapter for the synthetic framework catalog."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

from neo4j import GraphDatabase

from .workflow import GraphCatalog, GraphSymbol, WorkflowRejection

ALLOWED_NEO4J_SCHEMES = {"bolt", "bolt+s", "neo4j", "neo4j+s"}

GET_FIXTURE_HASH_QUERY = """
MATCH (fixture:Fixture {fixtureId: $fixture_id})
RETURN fixture.fixtureHash AS fixture_hash
"""

UPSERT_FIXTURE_QUERY = """
MERGE (fixture:Fixture {fixtureId: $fixture_id})
SET fixture.version = $version,
    fixture.provenance = $provenance,
    fixture.license = $license,
    fixture.fixtureHash = $fixture_hash
WITH fixture
UNWIND $symbols AS row
MERGE (symbol:Symbol {qualifiedName: row.qualified_name, version: $version})
SET symbol.name = row.name,
    symbol.kind = row.kind
MERGE (fixture)-[:CONTAINS]->(symbol)
WITH symbol, row
UNWIND row.methods AS method_name
MERGE (method:Method {
  qualifiedName: row.qualified_name + '#' + method_name,
  version: $version
})
SET method.name = method_name
MERGE (symbol)-[:DEFINES]->(method)
"""

GET_SYMBOL_QUERY = """
MATCH (:Fixture {fixtureId: $fixture_id})-[:CONTAINS]->(symbol:Symbol {
  name: $name,
  version: $version
})
OPTIONAL MATCH (symbol)-[:DEFINES]->(method:Method)
RETURN symbol.name AS name,
       symbol.qualifiedName AS qualified_name,
       symbol.kind AS kind,
       collect(DISTINCT method.name) AS methods
"""

SEARCH_SYMBOLS_QUERY = """
MATCH (:Fixture {fixtureId: $fixture_id})-[:CONTAINS]->(symbol:Symbol {
  version: $version
})
OPTIONAL MATCH (symbol)-[:DEFINES]->(method:Method)
WITH symbol, collect(DISTINCT method.name) AS methods
WHERE toLower(symbol.name) CONTAINS toLower($search_text)
    OR toLower(symbol.qualifiedName) CONTAINS toLower($search_text)
    OR any(item IN methods WHERE toLower(item) CONTAINS toLower($search_text))
RETURN symbol.name AS name,
       symbol.qualifiedName AS qualified_name,
       symbol.kind AS kind,
       methods
ORDER BY symbol.name
LIMIT $limit
"""


class Neo4jCatalog:
    """Graph catalog with the same read contract as the JSON fixture catalog."""

    def __init__(
        self,
        driver: Any,
        fixture_id: str = "synthetic-java-test-framework-v1",
        version: str = "v1.0.0",
    ) -> None:
        self.driver = driver
        self.fixture_id = fixture_id
        self.version = version
        self.provenance = "Independently generated synthetic framework metadata"
        self.license = "CC0-1.0"

    @staticmethod
    def validate_uri(uri: str) -> None:
        parsed = urlsplit(uri)
        if parsed.scheme not in ALLOWED_NEO4J_SCHEMES or not parsed.hostname:
            raise ValueError("NEO4J_URI must use an allowed Neo4j scheme and host")
        if parsed.username or parsed.password:
            raise ValueError("NEO4J_URI must not embed credentials")

    @classmethod
    def from_env(cls, driver: Any = None) -> "Neo4jCatalog":
        values = {
            "NEO4J_URI": os.getenv("NEO4J_URI"),
            "NEO4J_USER": os.getenv("NEO4J_USER"),
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        }
        missing = sorted(name for name, value in values.items() if not value)
        if missing:
            raise ValueError("Missing required Neo4j environment variables: " + ", ".join(missing))
        uri = str(values["NEO4J_URI"])
        cls.validate_uri(uri)
        active_driver = driver or GraphDatabase.driver(
            uri,
            auth=(values["NEO4J_USER"], values["NEO4J_PASSWORD"]),
            max_connection_lifetime=300,
        )
        return cls(
            active_driver,
            fixture_id=os.getenv("GRAPH_FIXTURE_ID", "synthetic-java-test-framework-v1"),
            version=os.getenv("GRAPH_FIXTURE_VERSION", "v1.0.0"),
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connection(self) -> None:
        self.driver.verify_connectivity()

    def seed(self, catalog: GraphCatalog) -> dict[str, Any]:
        """Materialize one immutable synthetic fixture without clearing other data."""
        self.verify_connection()
        symbols = [
            {
                "name": symbol.name,
                "qualified_name": symbol.qualified_name,
                "kind": symbol.kind,
                "methods": list(symbol.methods),
            }
            for symbol in catalog.symbols
        ]
        with self.driver.session() as session:
            existing = session.run(GET_FIXTURE_HASH_QUERY, fixture_id=catalog.fixture_id).single()
            if existing and existing["fixture_hash"] != catalog.fixture_hash:
                raise ValueError("Fixture identity already exists with a different SHA-256")
            session.run(
                UPSERT_FIXTURE_QUERY,
                fixture_id=catalog.fixture_id,
                version=catalog.version,
                provenance=catalog.provenance,
                license=catalog.license,
                fixture_hash=catalog.fixture_hash,
                symbols=symbols,
            ).consume()
        self.fixture_id = catalog.fixture_id
        self.version = catalog.version
        return {
            "fixture_id": catalog.fixture_id,
            "fixture_hash": catalog.fixture_hash,
            "version": catalog.version,
            "symbol_count": len(symbols),
            "status": "seeded",
        }

    def get(self, name: str, version: str) -> GraphSymbol:
        if version != self.version:
            raise WorkflowRejection(
                "unsupported_version",
                f"Version {version!r} is not configured for the Neo4j backend",
            )
        with self.driver.session() as session:
            row = session.run(
                GET_SYMBOL_QUERY,
                fixture_id=self.fixture_id,
                name=name,
                version=version,
            ).single()
        if not row:
            raise WorkflowRejection(
                "missing_graph_context",
                f"Required symbol {name!r} is not present in Neo4j",
            )
        return GraphSymbol(
            name=row["name"],
            qualified_name=row["qualified_name"],
            kind=row["kind"],
            methods=tuple(sorted(item for item in row["methods"] if item)),
        )

    def search(self, query: str, version: str, limit: int = 8) -> list[dict[str, Any]]:
        if not query or len(query) > 80:
            raise WorkflowRejection("invalid_query", "Query must contain 1-80 characters")
        if not 1 <= limit <= 20:
            raise WorkflowRejection("invalid_limit", "Limit must be between 1 and 20")
        if version != self.version:
            raise WorkflowRejection(
                "unsupported_version",
                f"Version {version!r} is not configured for the Neo4j backend",
            )
        with self.driver.session() as session:
            rows = session.run(
                SEARCH_SYMBOLS_QUERY,
                fixture_id=self.fixture_id,
                version=version,
                search_text=query,
                limit=limit,
            )
            return [
                {
                    "name": row["name"],
                    "qualified_name": row["qualified_name"],
                    "kind": row["kind"],
                    "methods": sorted(item for item in row["methods"] if item),
                }
                for row in rows
            ]
