# Kiro SRE Monitor Agent - Makefile
# Development and deployment commands

.PHONY: help install test lint run deploy clean

# Default target
help:
	@echo "Kiro SRE Monitor Agent - Available commands:"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make run        - Run the agent locally"
	@echo "  make run-docker - Run with Docker"
	@echo "  make build      - Build Docker image"
	@echo "  make deploy     - Deploy to AWS"
	@echo "  make clean      - Clean temporary files"
	@echo ""

# Install dependencies
install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v --tb=short

# Run tests with coverage
test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=html

# Run linter
lint:
	ruff check src/ tests/

# Format code
format:
	ruff format src/ tests/

# Run the agent locally
run:
	uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Run with Docker
run-docker:
	docker-compose up

# Build Docker image
build:
	docker build -t kiro-sre-agent .

# Deploy to AWS (requires AWS credentials)
deploy:
	cd terraform && terraform init && terraform apply -auto-approve

# Deploy Lambda function
deploy-lambda:
	cd terraform && terraform apply -auto-approve -target=aws_lambda_function.kiro_agent

# Plan Terraform changes
plan:
	cd terraform && terraform plan

# Destroy infrastructure (DANGEROUS)
destroy:
	cd terraform && terraform destroy

# Clean temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info

# Generate logs for testing
generate-logs:
	curl -X POST http://localhost:8000/api/simulator/start?rps=5&error_rate=20

# Stop log generation
stop-logs:
	curl -X POST http://localhost:8000/api/simulator/stop

# Test webhook with chaos alert
test-webhook:
	curl -X POST http://localhost:8001/webhook/chaos

# Check agent health
health:
	curl http://localhost:8001/health

# View agent logs (Docker)
logs:
	docker-compose logs -f
