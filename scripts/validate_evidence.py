"""Validate public claims, evidence identities, split isolation, and privacy."""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.workflow import GenerationWorkflow, GraphCatalog  # noqa: E402

COMPILE_REQUEST = (
    "Create AcceptedGeneratedWorkflow as a Java test workflow in generated.tests "
    "backed by module accepted_generated and config testtables/AcceptedGenerated.toml "
    "for v1.0.0."
)
EVIDENCE_CLASSES = {
    "architecture",
    "historical",
    "measured",
    "reproduced",
    "target",
    "unsupported",
}
PRIVATE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"\bInfineon\b", re.IGNORECASE),
    re.compile(r"Rajendar\.Muddasani@", re.IGNORECASE),
    re.compile(r"Project10LocalOnly", re.IGNORECASE),
    re.compile(r"\bj:/", re.IGNORECASE),
)
SKIP_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "htmlcov",
    "pdocs",
    "tmp",
}
TEXT_SUFFIXES = {
    ".json",
    ".java",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def _load(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _sha256(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _resolve_pointer(payload: Any, pointer: str) -> Any:
    value = payload
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()[:24]
    if payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG file: {path.relative_to(ROOT)}")
    return struct.unpack(">II", payload[16:24])


def _public_text_files() -> list[Path]:
    files = []
    for directory, directory_names, file_names in os.walk(ROOT):
        directory_names[:] = [
            name
            for name in directory_names
            if name not in SKIP_DIRECTORIES and not name.endswith(".egg-info")
        ]
        parent = Path(directory)
        for file_name in file_names:
            path = parent / file_name
            if path.suffix.lower() in TEXT_SUFFIXES or path.name in {
                ".env.example",
                ".gitignore",
                "Dockerfile",
                "Makefile",
            }:
                files.append(path)
    return sorted(files)


def _validate_claims(
    claims: dict[str, Any],
    evaluation: dict[str, Any],
) -> int:
    checked_claims = 0
    artifact_cache: dict[str, dict[str, Any]] = {}
    for claim in claims["claims"]:
        if claim["evidence_class"] not in EVIDENCE_CLASSES:
            raise ValueError(f"Unknown evidence class for {claim['id']}")
        artifact_path = ROOT / claim["artifact"]
        if not artifact_path.exists():
            raise FileNotFoundError(f"Missing claim artifact: {claim['artifact']}")
        pointer = claim.get("json_pointer")
        if pointer:
            artifact = artifact_cache.setdefault(
                claim["artifact"], _load(claim["artifact"])
            )
            observed = _resolve_pointer(artifact, pointer)
            if observed != claim["value"]:
                raise ValueError(
                    f"Claim {claim['id']} expected {claim['value']!r}, got {observed!r}"
                )
        if claim["public_allowed"] and not claim.get("allowed_wording"):
            raise ValueError(f"Public claim lacks allowed wording: {claim['id']}")
        checked_claims += 1

    for boundary in claims["boundaries"]:
        if boundary["evidence_class"] not in {"target", "unsupported"}:
            raise ValueError(f"Boundary must be target or unsupported: {boundary['id']}")
        if boundary["public_allowed"]:
            raise ValueError(f"Unsupported boundary marked public: {boundary['id']}")

    if claims["base_sha"] != evaluation["base_sha"]:
        raise ValueError("Claim ledger base SHA differs from canonical evaluation")
    if claims["policy_identity"] != evaluation["policy_identity"]:
        raise ValueError("Claim ledger policy identity differs from canonical evaluation")
    return checked_claims


def validate() -> dict[str, Any]:
    claims = _load("evidence/claims.json")
    evaluation = _load("evidence/task_evaluation.json")
    trace = _load("evidence/evaluation_trace.json")
    benchmark = _load("evidence/mcp_benchmark.json")
    neo4j = _load("evidence/neo4j_integration.json")
    compile_report = _load("evidence/java_compile.json")
    fixture = _load("fixtures/evaluation_cases.json")

    checked_claims = _validate_claims(claims, evaluation)
    expected_hashes = {
        "benchmark_sha256": _sha256("fixtures/evaluation_cases.json"),
        "graph_fixture_sha256": _sha256("fixtures/synthetic_graph.json"),
        "protocol_sha256": _sha256("evidence/evaluation_protocol.json"),
    }
    if evaluation["artifacts"] != expected_hashes:
        raise ValueError("Canonical evaluation input hashes do not match repository files")

    if evaluation["selection"]["selected_candidate"] != "strict_graph_v2":
        raise ValueError("Unexpected selected policy")
    if evaluation["selection"]["confirmation_opened_for"] != ["strict_graph_v2"]:
        raise ValueError("Confirmation was not isolated to the selected policy")
    if set(trace["confirmation"]) != {"strict_graph_v2"}:
        raise ValueError("Trace contains non-selected confirmation candidates")
    if len(trace["confirmation"]["strict_graph_v2"]) != 32:
        raise ValueError("Confirmation trace must contain exactly 32 cases")

    groups = {
        split: {case["group"] for case in fixture["cases"] if case["split"] == split}
        for split in ("development", "validation", "confirmation")
    }
    if not (
        groups["development"].isdisjoint(groups["validation"])
        and groups["development"].isdisjoint(groups["confirmation"])
        and groups["validation"].isdisjoint(groups["confirmation"])
    ):
        raise ValueError("Evaluation groups overlap across splits")

    graph = GraphCatalog.from_path(ROOT / "fixtures" / "synthetic_graph.json")
    generated = GenerationWorkflow(graph).run_text(COMPILE_REQUEST)
    generated_hash = hashlib.sha256(generated["source"].encode("utf-8")).hexdigest()
    if compile_report["status"] != "passed":
        raise ValueError("Canonical Java compile did not pass")
    if compile_report["generated_source_sha256"] != generated_hash:
        raise ValueError("Compiled Java source identity differs from current generator")
    if compile_report["graph_fixture_sha256"] != graph.fixture_hash:
        raise ValueError("Java compile graph identity differs from current fixture")

    if neo4j["status"] != "passed" or neo4j["fixture_sha256"] != graph.fixture_hash:
        raise ValueError("Live Neo4j evidence does not match the current graph fixture")
    if benchmark["backend"] != "neo4j":
        raise ValueError("Canonical MCP benchmark did not use the live Neo4j backend")
    if benchmark["task_success_count"] != benchmark["request_count"]:
        raise ValueError("MCP benchmark contains failed tasks")
    if benchmark["protocol_error_count"] != 0:
        raise ValueError("MCP benchmark contains protocol errors")
    if benchmark["external_model_calls"] != 0:
        raise ValueError("Accepted policy unexpectedly called an external model")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_readme_values = (
        "96 CC0 synthetic intents",
        "32/32 bounded tasks",
        "24/24 supported intents",
        "8/8 adversarial or unsupported intents",
        "29.13 / 48.61 / 54.23 ms",
        "0 calls; $0 model API cost",
    )
    missing_values = [value for value in required_readme_values if value not in readme]
    if missing_values:
        raise ValueError(f"README is missing canonical wording: {missing_values}")

    required_docs = (
        "docs/ARCHITECTURE.md",
        "docs/DATA_CARD.md",
        "docs/DEPLOYMENT.md",
        "docs/MCP_INTEGRATION.md",
        "docs/POLICY_CARD.md",
        "evidence/METRIC_IMPROVEMENT_PLAN.md",
        "evidence/PDF_REPOSITORY_AUDIT.md",
    )
    for relative_path in required_docs:
        if not (ROOT / relative_path).is_file():
            raise FileNotFoundError(f"Missing required public document: {relative_path}")

    required_images = (
        "assets/evaluation-candidates.png",
        "assets/mcp-generation-workflow.png",
    )
    for relative_path in required_images:
        if _png_dimensions(ROOT / relative_path) != (1600, 930):
            raise ValueError(f"Unexpected evidence image dimensions: {relative_path}")

    removed_artifacts = (
        "assets/neo4j-graph-schema.png",
        "assets/neo4j-graph-visualization.png",
        "examples/01_quick_start.ipynb",
        "examples/02_advanced_queries.ipynb",
        "examples/03_mcp_code_generation.ipynb",
        "examples/generated_code/ExampleGeneratedTestMethod.java",
        "scripts/seed_neo4j.py",
    )
    existing_stale = [path for path in removed_artifacts if (ROOT / path).exists()]
    if existing_stale:
        raise ValueError(f"Stale artifacts remain: {existing_stale}")

    public_files = _public_text_files()
    for path in public_files:
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                raise ValueError(
                    f"Private marker {pattern.pattern!r} found in {path.relative_to(ROOT)}"
                )

    tracked_private = subprocess.run(
        ["git", "ls-files", "--", "pdocs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout.strip()
    if tracked_private:
        raise ValueError("Private pdocs content is tracked")
    ignored_private = subprocess.run(
        ["git", "check-ignore", "pdocs/PRIVATE_PROJECT_BRIEF.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if ignored_private.returncode != 0:
        raise ValueError("pdocs is not ignored")

    return {
        "status": "passed",
        "claims_checked": checked_claims,
        "boundaries_checked": len(claims["boundaries"]),
        "evidence_json_files": len(list((ROOT / "evidence").glob("*.json"))),
        "confirmation_cases": len(trace["confirmation"]["strict_graph_v2"]),
        "privacy_patterns_checked": len(PRIVATE_PATTERNS),
        "public_text_files_scanned": len(public_files),
        "public_images_checked": len(required_images),
        "pdocs_ignored_and_untracked": True,
    }


def main() -> int:
    print(json.dumps(validate(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
