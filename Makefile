.PHONY: setup dev test lint format check

setup:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov=ai_engine tests/

lint:
	ruff check .

format:
	ruff format .

check: lint test
