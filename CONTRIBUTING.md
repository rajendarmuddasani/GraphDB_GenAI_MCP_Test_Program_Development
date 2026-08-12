# Contributing

Contributions should preserve the bounded, synthetic, evidence-backed MCP workflow.

## Principles

- keep examples sanitized and publishable,
- prefer small, reviewable pull requests,
- update documentation when behavior changes,
- retain failed candidate results and predeclared selection rules,
- avoid internal-only workflow notes or interview-preparation material,
- never weaken a rejection or validation gate only to improve task-success metrics.

## Development Flow

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
pytest --cov=src --cov-report=term-missing --cov-fail-under=75
ruff check src tests scripts
python scripts/validate_evidence.py
pip-audit -r requirements.txt --progress-spinner off
bandit -r src scripts -q -ll
```

On Windows, activate with `.\.venv\Scripts\Activate.ps1`.

## Pull Request Expectations

- describe the problem being solved,
- include exact validation commands and results,
- keep public docs aligned with the actual repository structure,
- update `claims.json` only when a canonical artifact supports the new value,
- disclose synthetic/public data provenance and licenses,
- include failed/no-improvement trials when selection behavior changes,
- avoid speculative capability, scale, latency, adoption, or business-impact claims.

Changes to intent grammar, graph schema, candidate selection, generation, validation, or MCP responses require focused tests and a regenerated independent confirmation artifact. Do not tune repeatedly against the existing confirmation split.