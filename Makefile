.PHONY: help install install-dev test test-verbose test-coverage lint format clean build run docker-build docker-run

# Default target
help:
	@echo "PubMed MCP Server - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install production dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  run         - Run the server"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-coverage - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code with black"
	@echo ""
	@echo "Build & Clean:"
	@echo "  build       - Build package"
	@echo "  clean       - Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Development setup
install:
	pip install -r requirements.txt

install-dev: install
	pip install -e .
	pip install black isort mypy flake8

# Run the server
run:
	python -m src.main

# Testing
test:
	python -m pytest tests/ -v

test-verbose:
	python -m pytest tests/ -v --tb=long

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

# Build and clean
build:
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker support
docker-build:
	docker build -t pubmed-mcp .

docker-run:
	docker run -it --rm -e PUBMED_API_KEY=$(PUBMED_API_KEY) -e PUBMED_EMAIL=$(PUBMED_EMAIL) pubmed-mcp
