.PHONY: lambda
# Build binary for AWS Lambda
lambda:
	cargo build --release --target x86_64-unknown-linux-musl
	rm -f bootstrap; rm -f lambda.zip
	cp target/x86_64-unknown-linux-musl/release/nationguessr target/bootstrap
	zip -j target/lambda.zip target/bootstrap

.PHONY: clean
# Remove all build artifacts
clean:
	rm -rf target/
	rm Cargo.lock

.PHONY: ci
# Run essential checks on each commit
ci: check lint test

.PHONY: check
# Perform project files borrow-checking without binary building
check:
	cargo check

.PHONY: lint
# Verify proper formatting for source files with Cargo Clippy
lint:
	cargo clippy

.PHONY: format
# Automatic fix linting erros for all source files
format:
	cargo clippy --fix

.PHONY: test
# Run all project test suites
test:
	cargo test

