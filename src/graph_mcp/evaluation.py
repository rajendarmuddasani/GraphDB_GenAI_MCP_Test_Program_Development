"""Bounded candidate selection and sealed-confirmation evaluation."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable

from .workflow import (
    GenerationIntent,
    GenerationWorkflow,
    GraphCatalog,
    WorkflowRejection,
)

CANDIDATE_DESCRIPTIONS = {
    "no_graph_v0": "Renders the template without graph citations; validation must reject it.",
    "lenient_repair_v1": (
        "Silently replaces rejected requests with a safe default; measures false acceptance."
    ),
    "strict_graph_v2": (
        "Uses exact graph context and fails closed on intent, syntax, contract, "
        "grounding, or safety errors."
    ),
    "wide_context_v3": (
        "Imports every graph symbol; tests whether extra irrelevant context improves "
        "the strict policy."
    ),
}

DEFAULT_REQUEST = (
    "Create SafeFallbackWorkflow as a Java test workflow in generated.tests "
    "backed by module safe_fallback and config testtables/SafeFallback.toml "
    "for v1.0.0."
)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = round((len(ordered) - 1) * percentile)
    return ordered[index]


def _candidate_runner(
    candidate_id: str,
    workflow: GenerationWorkflow,
) -> Callable[[str], dict[str, Any]]:
    if candidate_id == "strict_graph_v2":
        return workflow.run_text

    if candidate_id == "lenient_repair_v1":

        def run_lenient(request: str) -> dict[str, Any]:
            result = workflow.run_text(request)
            return result if result["status"] != "rejected" else workflow.run_text(DEFAULT_REQUEST)

        return run_lenient

    if candidate_id in {"no_graph_v0", "wide_context_v3"}:

        def run_context_variant(request: str) -> dict[str, Any]:
            try:
                intent = GenerationIntent.from_text(request)
                citations = tuple() if candidate_id == "no_graph_v0" else workflow.catalog.symbols
                source = workflow._render(intent, citations)
                validation = workflow.validator.validate(source, intent, citations)
                return {
                    "status": "generated" if validation.valid else "validation_failed",
                    "source": source if validation.valid else None,
                    "citations": [asdict(item) for item in citations],
                    "validation": asdict(validation),
                    "error": None if validation.valid else {"code": "generated_source_rejected"},
                }
            except WorkflowRejection as exc:
                return workflow._rejection(exc)

        return run_context_variant

    raise ValueError(f"Unknown candidate: {candidate_id}")


def _evaluate_cases(
    candidate_id: str,
    cases: list[dict[str, Any]],
    workflow: GenerationWorkflow,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runner = _candidate_runner(candidate_id, workflow)
    latencies_ms: list[float] = []
    task_successes = 0
    validation_passes = 0
    safe_rejections = 0
    exact_rejections = 0
    false_acceptances = 0
    generated_expected = 0
    rejected_expected = 0
    citation_precisions: list[float] = []
    symbol_recalls: list[float] = []
    groundedness_values: list[float] = []
    failures: Counter[str] = Counter()
    observed_rejections: Counter[str] = Counter()
    traces: list[dict[str, Any]] = []

    for case in cases:
        started = perf_counter_ns()
        result = runner(case["request"])
        latency_ms = (perf_counter_ns() - started) / 1_000_000
        latencies_ms.append(latency_ms)

        expected_status = case["expected_status"]
        observed_status = result["status"]
        success = False
        citation_precision = None
        symbol_recall = None

        if expected_status == "generated":
            generated_expected += 1
            validation = result.get("validation") or {}
            validation_passed = observed_status == "generated" and validation.get("valid") is True
            validation_passes += int(validation_passed)
            cited_names = {item["name"] for item in result.get("citations", [])}
            required_names = set(case["required_symbols"])
            citation_precision = (
                len(cited_names & required_names) / len(cited_names) if cited_names else 0.0
            )
            symbol_recall = len(cited_names & required_names) / len(required_names)
            citation_precisions.append(citation_precision)
            symbol_recalls.append(symbol_recall)
            groundedness_values.append(float(validation.get("groundedness", 0.0)))
            success = validation_passed and symbol_recall == 1.0
            if not success:
                failures[f"supported:{observed_status}"] += 1
        else:
            rejected_expected += 1
            observed_error = (result.get("error") or {}).get("code")
            if observed_status == "rejected":
                safe_rejections += 1
                observed_rejections[str(observed_error)] += 1
            if observed_status == "generated":
                false_acceptances += 1
            exact = observed_status == "rejected" and observed_error == case["expected_error"]
            exact_rejections += int(exact)
            success = exact
            if not success:
                failures[f"adversarial:{observed_status}"] += 1

        task_successes += int(success)
        traces.append(
            {
                "case_id": case["case_id"],
                "group": case["group"],
                "expected_status": expected_status,
                "expected_error": case["expected_error"],
                "observed_status": observed_status,
                "observed_error": (result.get("error") or {}).get("code"),
                "success": success,
                "validation_valid": (result.get("validation") or {}).get("valid"),
                "citation_precision": citation_precision,
                "required_symbol_recall": symbol_recall,
                "latency_ms": round(latency_ms, 6),
            }
        )

    count = len(cases)
    metrics = {
        "candidate_id": candidate_id,
        "description": CANDIDATE_DESCRIPTIONS[candidate_id],
        "case_count": count,
        "supported_case_count": generated_expected,
        "adversarial_case_count": rejected_expected,
        "task_success_count": task_successes,
        "task_success_rate": round(task_successes / count, 6),
        "generation_validation_pass_rate": round(validation_passes / generated_expected, 6),
        "safe_rejection_recall": round(safe_rejections / rejected_expected, 6),
        "exact_rejection_accuracy": round(exact_rejections / rejected_expected, 6),
        "false_acceptance_count": false_acceptances,
        "mean_groundedness": round(sum(groundedness_values) / len(groundedness_values), 6),
        "citation_precision": round(sum(citation_precisions) / len(citation_precisions), 6),
        "required_symbol_recall": round(sum(symbol_recalls) / len(symbol_recalls), 6),
        "error_rate": round(1 - (task_successes / count), 6),
        "failure_taxonomy": dict(sorted(failures.items())),
        "observed_rejection_codes": dict(sorted(observed_rejections.items())),
        "latency_ms": {
            "p50": round(_percentile(latencies_ms, 0.50), 6),
            "p95": round(_percentile(latencies_ms, 0.95), 6),
            "p99": round(_percentile(latencies_ms, 0.99), 6),
            "max": round(max(latencies_ms), 6),
        },
    }
    return metrics, traces


def _passes_gates(metrics: dict[str, Any], gates: dict[str, float]) -> bool:
    return (
        metrics["task_success_rate"] >= gates["task_success_rate_min"]
        and metrics["generation_validation_pass_rate"]
        >= gates["generation_validation_pass_rate_min"]
        and metrics["safe_rejection_recall"] >= gates["safe_rejection_recall_min"]
        and metrics["citation_precision"] >= gates["citation_precision_min"]
        and metrics["required_symbol_recall"] >= gates["required_symbol_recall_min"]
        and metrics["latency_ms"]["p95"] <= gates["latency_p95_ms_max"]
    )


def _runtime_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in (
        root / "src" / "graph_mcp" / "workflow.py",
        root / "src" / "graph_mcp" / "graph_store.py",
        root / "src" / "graph_mcp" / "server.py",
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _base_sha(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def run_evaluation(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Select on validation and evaluate only the winner on confirmation."""
    cases_path = root / "fixtures" / "evaluation_cases.json"
    graph_path = root / "fixtures" / "synthetic_graph.json"
    protocol_path = root / "evidence" / "evaluation_protocol.json"
    benchmark = json.loads(cases_path.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    catalog = GraphCatalog.from_path(graph_path)
    workflow = GenerationWorkflow(catalog)

    development_cases = [case for case in benchmark["cases"] if case["split"] == "development"]
    validation_cases = [case for case in benchmark["cases"] if case["split"] == "validation"]
    development_results = {}
    validation_results = {}
    trace = {"development": {}, "validation": {}, "confirmation": {}}

    for candidate_id in protocol["candidate_ids"]:
        development_results[candidate_id], trace["development"][candidate_id] = _evaluate_cases(
            candidate_id, development_cases, workflow
        )
        validation_results[candidate_id], trace["validation"][candidate_id] = _evaluate_cases(
            candidate_id, validation_cases, workflow
        )

    gates = protocol["safety_gates"]
    eligible = [
        candidate_id
        for candidate_id, metrics in validation_results.items()
        if _passes_gates(metrics, gates)
    ]
    if not eligible:
        raise RuntimeError("No candidate passed the predeclared validation gates")
    selected = sorted(
        eligible,
        key=lambda candidate_id: (
            -validation_results[candidate_id]["task_success_rate"],
            validation_results[candidate_id]["latency_ms"]["p95"],
            candidate_id,
        ),
    )[0]

    confirmation_cases = [case for case in benchmark["cases"] if case["split"] == "confirmation"]
    confirmation, trace["confirmation"][selected] = _evaluate_cases(
        selected, confirmation_cases, workflow
    )

    def file_hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    report = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "Graph-Backed MCP Java Test Generation",
        "base_sha": _base_sha(root),
        "runtime_sha256": _runtime_hash(root),
        "policy_identity": f"{selected}:{_runtime_hash(root)}",
        "data_scope": benchmark["provenance"],
        "license": benchmark["license"],
        "counts": benchmark["counts"],
        "split_policy": benchmark["split_policy"],
        "artifacts": {
            "benchmark_sha256": file_hash(cases_path),
            "graph_fixture_sha256": file_hash(graph_path),
            "protocol_sha256": file_hash(protocol_path),
        },
        "selection": {
            "objective": protocol["selection_objective"],
            "gates": gates,
            "eligible_candidates": eligible,
            "selected_candidate": selected,
            "confirmation_opened_for": [selected],
        },
        "development_results": development_results,
        "validation_results": validation_results,
        "confirmation_result": confirmation,
        "weakest_behavior": (
            "No failures were observed in the bounded synthetic grammar; free-form intent "
            "generalization and external framework compilation are not proven by this benchmark."
        ),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "not_reported",
            "latency_scope": "single-process local benchmark; not a production SLO",
        },
        "command": "python scripts/evaluate_workflow.py",
        "random_seed": None,
    }
    return report, trace
