import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_evidence import validate  # noqa: E402


def test_public_evidence_contract():
    result = validate()

    assert result["status"] == "passed"
    assert result["claims_checked"] == 14
    assert result["boundaries_checked"] == 5
    assert result["confirmation_cases"] == 32
    assert result["public_images_checked"] == 2
    assert result["pdocs_ignored_and_untracked"] is True
