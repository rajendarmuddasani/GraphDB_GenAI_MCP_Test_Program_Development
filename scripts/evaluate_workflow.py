"""Run candidate selection and write canonical evaluation evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.evaluation import run_evaluation  # noqa: E402


def main() -> int:
    report, trace = run_evaluation(ROOT)
    evaluation_path = ROOT / "evidence" / "task_evaluation.json"
    trace_path = ROOT / "evidence" / "evaluation_trace.json"
    evaluation_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    trace_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    confirmation = report["confirmation_result"]
    print(
        json.dumps(
            {
                "selected_candidate": report["selection"]["selected_candidate"],
                "confirmation_task_success_rate": confirmation["task_success_rate"],
                "confirmation_safe_rejection_recall": confirmation["safe_rejection_recall"],
                "confirmation_latency_p95_ms": confirmation["latency_ms"]["p95"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
