from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from neo4j_agent import Neo4jAgent


class _FakeResult:
    def single(self):
        return {"ok": 1}


class _FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def run(self, cypher, parameters=None):
        return _FakeResult()


class _FakeDriver:
    def session(self):
        return _FakeSession()

    def close(self):
        return None


def test_collect_project_snapshot_counts_java_files_and_dependencies():
    sample_project = ROOT / "examples" / "sample_project"
    build_xml = sample_project / "build.xml"

    snapshot = Neo4jAgent.collect_project_snapshot(sample_project, build_xml)

    assert snapshot["java_file_count"] >= 1
    assert snapshot["build_dependency_count"] == 4
    assert "src/testmethod" in snapshot["packages"]


def test_collect_project_snapshot_rejects_missing_paths(tmp_path):
    missing_dir = tmp_path / "missing-project"
    missing_build = tmp_path / "missing-build.xml"

    with pytest.raises(FileNotFoundError):
        Neo4jAgent.collect_project_snapshot(missing_dir, missing_build)


def test_from_env_uses_environment_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NEO4J_URI=bolt://localhost:7687\n"
        "NEO4J_USER=neo4j\n"
        "NEO4J_PASSWORD=test-password\n",
        encoding="utf-8",
    )

    agent = Neo4jAgent.from_env(env_file=str(env_file), driver=_FakeDriver())

    assert agent.uri == "bolt://localhost:7687"
    assert agent.user == "neo4j"


def test_verify_connection_returns_connected_status():
    agent = Neo4jAgent(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test-password",
        driver=_FakeDriver(),
    )

    status = agent.verify_connection()

    assert status == {
        "connected": True,
        "uri": "bolt://localhost:7687",
    }