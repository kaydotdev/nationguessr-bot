.PHONY: clean
# Remove all processing artifacts, build files and cache files
clean:
	rm -rf .ruff_cache/ .pytest_cache/
	find . -type d -name '__pycache__' -exec rm -rf {} +

.PHONY: ci
# Full continuous integration pipeline
ci: lint test

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

.PHONY: test
# Run all project test suites
test:
	pytest tests/

.PHONY: requirements
# Export project dependencies in `requirements.txt` format for the virtual environments
requirements:
	poetry export -f requirements.txt --without=dev --without-hashes --without-urls --output requirements.txt

.PHONY: serve
# Run Telegram bot script in polling mode
# Used solely for manual testing in a local environment
serve:
	cd src && python main.py
