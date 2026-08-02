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

# ── Additional coverage ───────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PROJECT = ROOT / "examples" / "sample_project"
BUILD_XML = SAMPLE_PROJECT / "build.xml"


def _agent() -> Neo4jAgent:
    return Neo4jAgent(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test-password",
        driver=_FakeDriver(),
    )


def test_ingest_project_returns_preflight_report():
    agent = _agent()
    report = agent.ingest_project("1.0.0", SAMPLE_PROJECT, BUILD_XML)
    assert report["status"] == "preflight_complete"
    assert report["version"] == "1.0.0"
    assert "project_snapshot" in report


def test_ingest_project_snapshot_embedded():
    agent = _agent()
    report = agent.ingest_project("2.0", SAMPLE_PROJECT, BUILD_XML)
    snapshot = report["project_snapshot"]
    assert snapshot["java_file_count"] >= 1
    assert snapshot["build_dependency_count"] == 4


def test_ingest_project_missing_dir_raises():
    import pytest
    agent = _agent()
    with pytest.raises(FileNotFoundError):
        agent.ingest_project("1.0", "/nonexistent/path", BUILD_XML)


def test_query_returns_list():
    class _IterableResult:
        def __iter__(self):
            return iter([])

    class _IterableSession(_FakeSession):
        def run(self, cypher, parameters=None):
            return _IterableResult()

    class _IterableDriver:
        def session(self):
            return _IterableSession()
        def close(self):
            return None

    agent = Neo4jAgent(uri="bolt://x", user="u", password="p",
                       driver=_IterableDriver())
    results = agent.query("RETURN 1 AS n")
    assert isinstance(results, list)


def test_extract_build_dependencies_count():
    deps = Neo4jAgent._extract_build_dependencies(BUILD_XML)
    assert len(deps) == 4


def test_extract_build_dependencies_returns_sorted():
    deps = Neo4jAgent._extract_build_dependencies(BUILD_XML)
    assert deps == sorted(deps)


def test_context_manager_calls_close():
    closed = []

    class _TrackingDriver(_FakeDriver):
        def close(self):
            closed.append(True)

    with Neo4jAgent(uri="bolt://x", user="u", password="p",
                    driver=_TrackingDriver()):
        pass

    assert len(closed) == 1


def test_from_env_raises_on_missing_vars(tmp_path, monkeypatch):
    # Ensure the required vars are absent from the process environment
    for var in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("NEO4J_URI=bolt://localhost:7687\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Neo4jAgent.from_env(env_file=str(env_file), driver=_FakeDriver())


def test_collect_snapshot_rejects_non_xml(tmp_path):
    import pytest
    build_txt = tmp_path / "build.txt"
    build_txt.write_text("not xml")
    with pytest.raises(ValueError):
        Neo4jAgent.collect_project_snapshot(SAMPLE_PROJECT, build_txt)


def test_build_parser_subcommands():
    from neo4j_agent import build_parser
    parser = build_parser()
    args = parser.parse_args([
        "preflight",
        "--version", "1.0",
        "--project-path", str(SAMPLE_PROJECT),
        "--build-xml-path", str(BUILD_XML),
    ])
    assert args.command == "preflight"
    assert args.version == "1.0"
