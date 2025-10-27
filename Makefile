.PHONY: help setup docker-build docker-up docker-down docker-logs docker-shell run clean test

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)DBT MCP Server - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

setup: ## Run the setup script for local installation
	@echo "$(BLUE)Running setup script...$(NC)"
	@chmod +x setup.sh
	@./setup.sh

install: ## Install dependencies manually (requires uv)
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@uv venv
	@. .venv/bin/activate && uv pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN).env file created from template$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

##@ Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker-compose build
	@echo "$(GREEN)Docker image built!$(NC)"

docker-build-nc: ## Build Docker image without cache
	@echo "$(BLUE)Building Docker image (no cache)...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)Docker image built!$(NC)"

docker-up: ## Start Docker containers in detached mode
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Containers started!$(NC)"

docker-run: env ## Run DBT BigQuery container interactively
	@echo "$(BLUE)Starting DBT BigQuery container...$(NC)"
	@docker-compose run --rm dbt-bigquery

docker-down: ## Stop and remove Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Containers stopped!$(NC)"

docker-down-v: ## Stop containers and remove volumes
	@echo "$(BLUE)Stopping containers and removing volumes...$(NC)"
	@docker-compose down -v
	@echo "$(GREEN)Containers and volumes removed!$(NC)"

docker-logs: ## View Docker container logs
	@docker-compose logs -f

docker-shell: ## Access Docker container shell
	@docker-compose exec dbt-bigquery /bin/bash

docker-restart: ## Restart Docker containers
	@echo "$(BLUE)Restarting Docker containers...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)Containers restarted!$(NC)"

##@ Local Development

run: ## Run DBT locally (requires virtual environment)
	@echo "$(BLUE)Activating virtual environment...$(NC)"
	@echo "$(YELLOW)Run DBT commands manually after activating:$(NC)"
	@echo "  source .venv/bin/activate"
	@echo "  dbt debug"
	@echo "  dbt run"

activate: ## Show command to activate virtual environment
	@echo "Run this command to activate the virtual environment:"
	@echo "  $(GREEN)source .venv/bin/activate$(NC)"

##@ DBT Commands

dbt-debug: ## Test DBT connection (Docker)
	@docker-compose exec dbt-bigquery dbt debug

dbt-deps: ## Install DBT dependencies (Docker)
	@docker-compose exec dbt-bigquery dbt deps

dbt-build: ## Run dbt build (Docker)
	@docker-compose exec dbt-bigquery dbt build

dbt-run: ## Run dbt models (Docker)
	@docker-compose exec dbt-bigquery dbt run

dbt-test: ## Run dbt tests (Docker)
	@docker-compose exec dbt-bigquery dbt test

dbt-docs: ## Generate dbt docs (Docker)
	@docker-compose exec dbt-bigquery dbt docs generate

dbt-clean: ## Clean dbt artifacts (Docker)
	@docker-compose exec dbt-bigquery dbt clean

##@ Maintenance

clean: ## Clean local build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf .venv
	@rm -rf target
	@rm -rf dbt_packages
	@rm -rf logs
	@rm -rf __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleaned!$(NC)"

clean-all: clean docker-down-v ## Clean everything including Docker volumes
	@echo "$(GREEN)All cleaned!$(NC)"

check: ## Check environment and dependencies
	@echo "$(BLUE)Checking environment...$(NC)"
	@echo "Python: $$(python3 --version 2>&1 || echo 'Not found')"
	@echo "Docker: $$(docker --version 2>&1 || echo 'Not found')"
	@echo "Docker Compose: $$(docker-compose --version 2>&1 || echo 'Not found')"
	@echo "uv: $$(uv --version 2>&1 || echo 'Not found')"
	@echo "uvx: $$(uvx --version 2>&1 || echo 'Not found')"
	@echo "dbt: $$(dbt --version 2>&1 | head -n1 || echo 'Not found')"
	@if [ -n "$$OPENAI_API_KEY" ]; then \
		echo "$(GREEN)OPENAI_API_KEY: Set$(NC)"; \
	else \
		echo "$(YELLOW)OPENAI_API_KEY: Not set$(NC)"; \
	fi

##@ Quick Start

quickstart-docker: env docker-build docker-run ## Quick start with Docker (recommended)

quickstart-local: setup run ## Quick start with local installation
