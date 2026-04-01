# Contributing

Contributions should keep the repository focused on reusable graph-backed developer tooling.

## Principles

- keep examples sanitized and publishable,
- prefer small, reviewable pull requests,
- update documentation when behavior changes,
- avoid adding internal-only workflow notes or interview-preparation material.

## Development Flow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Pull Request Expectations

- describe the problem being solved,
- include validation notes,
- keep public docs aligned with the actual repository structure,
- avoid speculative feature claims that the code does not support.