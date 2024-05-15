APP_NAME ?= nationguessr


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
	black --diff --check src/ tests/ scripts/ -q
	ruff check .

.PHONY: format
# Automatic fix linting errors for all Python files
format:
	black src/ tests/ scripts/ -q
	ruff check --fix .

.PHONY: test
# Run all project test suites
test:
	pytest tests/

.PHONY: requirements
# Export project dependencies for production container
requirements:
	poetry export -f requirements.txt --only main --without-hashes --without-urls --output ./src/requirements.txt

.PHONY: serve
# Run Telegram bot script in polling mode
# Used solely for manual testing in a local environment
serve:
	cd src && python main.py

.PHONY: check-docker
# Checks if Docker is installed on the machine, otherwise returns error code
check-docker:
	@which docker >/dev/null || (echo "❌ Docker is not found on this machine" && exit 1)

.PHONY: check-aws
# Checks if AWS CLI is installed on the machine, otherwise returns error code
check-aws:
	@which aws >/dev/null || (echo "❌ AWS CLI is not found on this machine" && exit 1)

.PHONY: image
# Build a Docker image for serverless deployment
image: check-docker
	docker build -t $(APP_NAME) .

.PHONY: deploy
# Push production Docker image to the private ECR registry
deploy: check-docker check-aws image
	@if [ -z "${VAR_AWS_REGION}" ]; then \
		echo "❌ ECR region is not specified. Set it in the 'VAR_AWS_REGION' environment variable" && exit 1; \
	fi

	@if [ -z "${VAR_AWS_ACCOUNT_ID}" ]; then \
		echo "❌ AWS account ID is not specified. Set it in the 'VAR_AWS_ACCOUNT_ID' environment variable" && exit 1; \
	fi

	@aws ecr get-login-password --region ${VAR_AWS_REGION} | \
		docker login --username AWS --password-stdin ${VAR_AWS_ACCOUNT_ID}.dkr.ecr.${VAR_AWS_REGION}.amazonaws.com
	@docker tag $(APP_NAME):latest ${VAR_AWS_ACCOUNT_ID}.dkr.ecr.${VAR_AWS_REGION}.amazonaws.com/$(APP_NAME):latest
	@docker push ${VAR_AWS_ACCOUNT_ID}.dkr.ecr.${VAR_AWS_REGION}.amazonaws.com/$(APP_NAME):latest
