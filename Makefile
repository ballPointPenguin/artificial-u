# ArtificialU Development Makefile
# This Makefile provides convenient commands for common development tasks

# Variables
PYTHON := python3
UV := uv
PROJECT_NAME := artificial_u
FASTAPI_PORT ?= 8000
SRC_DIR := artificial_u
TEST_DIR := tests

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Artificial-U Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
.PHONY: setup
setup: ## Set up development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@$(UV) sync
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	@$(UV) run pre-commit install
	@echo "$(GREEN)Setup complete! Run 'make help' for available commands.$(NC)"

.PHONY: shell
shell: ## Show how to activate the project virtualenv
	@echo "$(GREEN)Activate the uv-managed virtualenv with:$(NC)"
	@echo "  source .venv/bin/activate"
	@echo "$(YELLOW)Or simply prefix commands with 'uv run' (no activation needed).$(NC)"

# Dependency Management
.PHONY: deps-lock
deps-lock: ## Update uv.lock from pyproject.toml
	@echo "$(GREEN)Locking dependencies...$(NC)"
	@$(UV) lock
	@echo "$(GREEN)Dependencies locked!$(NC)"

.PHONY: deps-upgrade
deps-upgrade: ## Upgrade all dependencies in uv.lock
	@echo "$(GREEN)Upgrading dependencies...$(NC)"
	@$(UV) lock --upgrade
	@echo "$(GREEN)Dependencies upgraded! Run 'make deps-sync' to apply.$(NC)"

.PHONY: deps-sync
deps-sync: ## Sync environment with uv.lock
	@echo "$(GREEN)Syncing dependencies...$(NC)"
	@$(UV) sync --locked
	@echo "$(GREEN)Dependencies synced!$(NC)"

# Code Quality
.PHONY: format
format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(UV) run black $(SRC_DIR) $(TEST_DIR)
	@$(UV) run isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatted!$(NC)"

.PHONY: lint
lint: ## Run all linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	@$(UV) run black --check $(SRC_DIR) $(TEST_DIR)
	@$(UV) run isort --check-only $(SRC_DIR) $(TEST_DIR)
	@$(UV) run flake8 $(SRC_DIR)
	@echo "$(GREEN)Linting complete!$(NC)"

# Testing
.PHONY: test
test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	@$(UV) run pytest

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	@$(UV) run pytest -m unit

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	@$(UV) run pytest -m integration

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@$(UV) run pytest --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term

.PHONY: test-verbose
test-verbose: ## Run tests with verbose output
	@echo "$(GREEN)Running tests with verbose output...$(NC)"
	@$(UV) run pytest -v

# Database
.PHONY: db-setup
db-setup: ## Set up development database
	@echo "$(GREEN)Setting up development database...$(NC)"
	@$(UV) run python scripts/initialize_db.py
	@echo "$(GREEN)Database setup complete!$(NC)"

.PHONY: db-setup-test
db-setup-test: ## Set up test database
	@echo "$(GREEN)Setting up test database...$(NC)"
	@$(UV) run python scripts/setup_test_db.py
	@echo "$(GREEN)Test database setup complete!$(NC)"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	@$(UV) run python scripts/run_alembic.py upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

.PHONY: db-rebuild-dev
db-rebuild-dev: ## Rebuild development database
	@echo "$(GREEN)Rebuilding development database...$(NC)"
	@$(UV) run python scripts/rebuild_dev_db.py
	@echo "$(GREEN)Development database rebuilt!$(NC)"

# Docker Services
.PHONY: services-up
services-up: ## Start Docker services (postgres, minio)
	@echo "$(GREEN)Starting Docker services...$(NC)"
	@docker compose up -d

.PHONY: services-down
services-down: ## Stop Docker services
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	@docker compose down

.PHONY: services-logs
services-logs: ## View Docker services logs
	@echo "$(GREEN)Showing Docker services logs...$(NC)"
	@docker compose logs -f

.PHONY: services-restart
services-restart: ## Restart Docker services
	@echo "$(GREEN)Restarting Docker services...$(NC)"
	@docker compose restart

# Application
.PHONY: run-api
run-api: ## Run the FastAPI application
	@echo "$(GREEN)Starting FastAPI application...$(NC)"
	@$(UV) run uvicorn $(PROJECT_NAME).api.app:app --reload --reload-delay 1.0 --reload-dir $(SRC_DIR) --reload-include "*.py" --host 0.0.0.0 --port $(FASTAPI_PORT)

.PHONY: run-api-log
run-api-log: ## Run the FastAPI application and log output to api.log
	@echo "$(GREEN)Starting FastAPI application and logging to api.log...$(NC)"
	@$(MAKE) run-api 2>&1 | tee api.log

.PHONY: run-api-no-reload
run-api-no-reload: ## Run the FastAPI application without auto-reload
	@echo "$(GREEN)Starting FastAPI application (no reload)...$(NC)"
	@$(UV) run uvicorn $(PROJECT_NAME).api.app:app --host 0.0.0.0 --port $(FASTAPI_PORT)

.PHONY: run-worker
run-worker: ## Run the background worker
	@echo "$(GREEN)Starting background worker...$(NC)"
	@$(UV) run python -m $(PROJECT_NAME).api.worker

.PHONY: cli
cli: ## Run the CLI (use CLI=<command> for specific commands)
	@echo "$(GREEN)Running CLI command: $(CLI)$(NC)"
	@$(UV) run artificial_u $(CLI)

# Pre-commit
.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "$(GREEN)Running pre-commit hooks...$(NC)"
	@$(UV) run pre-commit run --all-files

.PHONY: pre-commit-update
pre-commit-update: ## Update pre-commit hooks
	@echo "$(GREEN)Updating pre-commit hooks...$(NC)"
	@$(UV) run pre-commit autoupdate

# Cleanup
.PHONY: clean
clean: ## Clean up temporary files and caches
	@echo "$(GREEN)Cleaning up temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

.PHONY: clean-all
clean-all: clean ## Clean everything including Docker volumes
	@echo "$(GREEN)Cleaning Docker volumes...$(NC)"
	@docker compose down -v 2>/dev/null || true
	@echo "$(GREEN)Full cleanup complete!$(NC)"

# Development Workflows
.PHONY: check
check: lint test ## Run linting and tests
	@echo "$(GREEN)All checks passed!$(NC)"

.PHONY: dev-setup
dev-setup: setup services-up db-setup ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and add your API keys"
	@echo "  2. Run 'make run-api' to start the application"
	@echo "  3. Run 'make cli CLI=\"--help\"' to explore CLI commands"

.PHONY: ci
ci: deps-sync lint test ## Run CI pipeline locally
	@echo "$(GREEN)CI pipeline complete!$(NC)"

# Quick commands for common tasks
.PHONY: quick-test
quick-test: ## Quick test run (unit tests only)
	@$(UV) run pytest -m unit -x --tb=short

.PHONY: mypy
mypy: ## Run mypy type checking
	@echo "$(GREEN)Running mypy type checking...$(NC)"
	@$(UV) run mypy $(SRC_DIR)

.PHONY: mypy-clean
mypy-clean: ## Run mypy with clean cache
	@echo "$(GREEN)Running mypy type checking with clean cache...$(NC)"
	@rm -rf .mypy_cache
	@$(UV) run mypy $(SRC_DIR)

.PHONY: quick-lint
quick-lint: ## Quick lint check (black and flake8 only)
	@$(UV) run black --check $(SRC_DIR) $(TEST_DIR) && $(UV) run flake8 $(SRC_DIR)
