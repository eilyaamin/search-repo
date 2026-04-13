.PHONY: install run test test-cov test-verbose clean

install:
	poetry install --no-root

run:
	poetry run python -m src.main

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

test-verbose:
	poetry run pytest -v

clean:
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
