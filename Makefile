.PHONY: lint
# Verify proper formatting for Python files
lint:
	black --diff --check src/ tests/ -q
	ruff check .


.PHONY: format
# Automatic fix linting errors for all Python files
format:
	black src/ tests/ -q
	ruff check --fix .
