import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graph_mcp.evaluation import run_evaluation  # noqa: E402


def test_predeclared_selection_and_confirmation_contract():
    report, trace = run_evaluation(ROOT)

    assert report["counts"] == {
        "total": 96,
        "development": 32,
        "validation": 32,
        "confirmation": 32,
        "supported_per_split": 24,
        "adversarial_per_split": 8,
    }
    assert report["selection"]["selected_candidate"] == "strict_graph_v2"
    assert report["selection"]["confirmation_opened_for"] == ["strict_graph_v2"]
    assert set(trace["confirmation"]) == {"strict_graph_v2"}

    validation = report["validation_results"]
    assert validation["no_graph_v0"]["generation_validation_pass_rate"] == 0.0
    assert validation["lenient_repair_v1"]["safe_rejection_recall"] == 0.0
    assert validation["wide_context_v3"]["citation_precision"] == 0.875
    assert validation["strict_graph_v2"]["task_success_rate"] == 1.0

    confirmation = report["confirmation_result"]
    assert confirmation["case_count"] == 32
    assert confirmation["task_success_rate"] == 1.0
    assert confirmation["generation_validation_pass_rate"] == 1.0
    assert confirmation["safe_rejection_recall"] == 1.0
    assert confirmation["citation_precision"] == 1.0
    assert confirmation["required_symbol_recall"] == 1.0
