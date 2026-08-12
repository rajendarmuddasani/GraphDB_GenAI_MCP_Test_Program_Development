.PHONY: setup lint test evidence security compile smoke check clean

PYTHON ?= python

setup:
	$(PYTHON) -m pip install --requirement requirements-dev.txt
	$(PYTHON) -m pip install --no-deps --editable .

lint:
	ruff check src tests scripts

test:
	pytest --cov=src --cov-report=term-missing --cov-fail-under=75

evidence:
	$(PYTHON) scripts/build_evaluation_fixture.py
	$(PYTHON) scripts/evaluate_workflow.py
	$(PYTHON) scripts/validate_evidence.py

security:
	pip-audit --requirement requirements.txt --progress-spinner off
	bandit --recursive src scripts --quiet --severity-level medium

compile:
	$(PYTHON) scripts/compile_generated.py --require-compiler

smoke:
	$(PYTHON) scripts/container_smoke.py $(PYTHON) -m graph_mcp.server

check: lint test security
	$(PYTHON) scripts/validate_evidence.py

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete 2>/dev/null; true
