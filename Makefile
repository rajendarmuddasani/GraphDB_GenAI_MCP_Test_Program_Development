.PHONY: setup lint test clean

setup:
	pip install pytest pytest-cov ruff python-dotenv neo4j

lint:
	ruff check src/ tests/ --select E,W,F --ignore E501

test:
	pytest tests/ -v --tb=short

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; find . -name '*.pyc' -delete 2>/dev/null; true
