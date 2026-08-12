"""Neo4j utilities for graph-backed Java test asset workflows.

The current module focuses on the public repository concerns that are useful on
their own:

- loading Neo4j connection details from environment variables,
- validating a project and producing a preflight snapshot,
- executing Cypher queries,
- checking whether the database is reachable.

It is intended as a clean starting point for richer ingestion pipelines rather
than a claim of a complete parser-backed implementation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from defusedxml import ElementTree as ET
from dotenv import load_dotenv
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jAgent:
    """Thin wrapper around the Neo4j Python driver."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        driver: Any = None,
    ):
        """Initialize a Neo4j client wrapper."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = driver or GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Neo4j agent initialized for %s", uri)

    @classmethod
    def from_env(
        cls,
        env_file: Optional[str] = None,
        driver: Any = None,
    ) -> "Neo4jAgent":
        """Build an agent from environment variables.

        Required variables are `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.
        """
        if env_file:
            load_dotenv(env_file, override=False)
        else:
            load_dotenv(override=False)

        required = {
            "NEO4J_URI": os.getenv("NEO4J_URI"),
            "NEO4J_USER": os.getenv("NEO4J_USER"),
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError("Missing required Neo4j environment variables: " + ", ".join(missing))

        return cls(
            uri=required["NEO4J_URI"],
            user=required["NEO4J_USER"],
            password=required["NEO4J_PASSWORD"],
            driver=driver,
        )

    def __enter__(self) -> "Neo4jAgent":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self):
        """Close Neo4j database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    @staticmethod
    def _resolve_existing_path(path_value: str | Path) -> Path:
        path = Path(path_value).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        return path

    @staticmethod
    def _extract_build_dependencies(build_xml_path: Path) -> list[str]:
        tree = ET.parse(build_xml_path)
        root = tree.getroot()
        dependencies = []
        for include in root.findall(".//include"):
            name = include.attrib.get("name")
            if name:
                dependencies.append(name)
        return sorted(set(dependencies))

    @staticmethod
    def collect_project_snapshot(
        project_path: str | Path,
        build_xml_path: str | Path,
    ) -> Dict[str, Any]:
        """Validate inputs and summarize the project that would be ingested."""
        resolved_project_path = Neo4jAgent._resolve_existing_path(project_path)
        resolved_build_xml_path = Neo4jAgent._resolve_existing_path(build_xml_path)

        if not resolved_project_path.is_dir():
            raise NotADirectoryError(f"Project path must be a directory: {resolved_project_path}")
        if resolved_build_xml_path.suffix.lower() != ".xml":
            raise ValueError(f"Build file must be an XML file: {resolved_build_xml_path}")

        java_files = sorted(resolved_project_path.rglob("*.java"))
        package_names = sorted(
            {
                java_file.parent.relative_to(resolved_project_path).as_posix() or "."
                for java_file in java_files
            }
        )
        build_dependencies = Neo4jAgent._extract_build_dependencies(resolved_build_xml_path)

        return {
            "project_root": str(resolved_project_path),
            "build_file": str(resolved_build_xml_path),
            "java_file_count": len(java_files),
            "sample_java_files": [
                str(java_file.relative_to(resolved_project_path)) for java_file in java_files[:10]
            ],
            "package_count": len(package_names),
            "packages": package_names,
            "build_dependency_count": len(build_dependencies),
            "build_dependencies": build_dependencies,
        }

    def ingest_project(
        self,
        version: str,
        project_path: str | Path,
        build_xml_path: str | Path,
    ) -> Dict[str, Any]:
        """Return a validated ingestion report scaffold.

        The public repository implementation intentionally stops at a preflight
        report. Extend this method with parser-backed extraction and graph
        persistence when integrating it into a fuller ingestion pipeline.
        """
        logger.info("Starting project preflight for version %s", version)
        snapshot = self.collect_project_snapshot(project_path, build_xml_path)

        report = {
            "status": "preflight_complete",
            "version": version,
            "classes_ingested": 0,
            "methods_extracted": 0,
            "dependencies_mapped": 0,
            "documentation_links": 0,
            "execution_time": 0.0,
            "project_snapshot": snapshot,
        }

        logger.info("Project preflight completed for %s", version)
        return report

    def verify_connection(self) -> Dict[str, Any]:
        """Run a minimal round-trip query to validate connectivity."""
        with self.driver.session() as session:
            record = session.run("RETURN 1 AS ok").single()
        return {
            "connected": bool(record and record["ok"] == 1),
            "uri": self.uri,
        }

    def query(
        self,
        cypher: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        """Execute a Cypher query and return row dictionaries."""
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for local workflows."""
    parser = argparse.ArgumentParser(description="Neo4j graph workflow utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser(
        "preflight",
        help="Validate a project and print a summary without needing Neo4j",
    )
    preflight.add_argument("--version", required=True)
    preflight.add_argument("--project-path", required=True)
    preflight.add_argument("--build-xml-path", required=True)

    health_check = subparsers.add_parser(
        "health-check",
        help="Verify the Neo4j connection from environment variables",
    )
    health_check.add_argument("--env-file", default=None)

    query_parser = subparsers.add_parser(
        "query",
        help="Execute a Cypher query using environment-based Neo4j settings",
    )
    query_parser.add_argument("--env-file", default=None)
    query_parser.add_argument("--cypher", required=True)

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "preflight":
        payload = Neo4jAgent.collect_project_snapshot(
            args.project_path,
            args.build_xml_path,
        )
        payload["version"] = args.version
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "health-check":
        with Neo4jAgent.from_env(env_file=args.env_file) as agent:
            print(json.dumps(agent.verify_connection(), indent=2))
        return 0

    if args.command == "query":
        with Neo4jAgent.from_env(env_file=args.env_file) as agent:
            result = agent.query(args.cypher)
            print(json.dumps(result, indent=2))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
