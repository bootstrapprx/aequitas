.PHONY: help up dev stop reset-db logs reset rebuild install-deps install-frontend install-backend clean-deps reinstall-frontend reinstall-backend shared services

# Default target
.DEFAULT_GOAL := help

# Default shell
SHELL := /bin/bash

# Variables
BACKEND_DIR = ./backend
FRONTEND_DIR = ./frontend
DOCKER_COMPOSE_DEV = ./docker-compose.dev.yml

# Colors for help output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help: ## Show this help message
	@echo ""
	@echo "$(GREEN)Aequitas Development Commands$(RESET)"
	@echo "=============================="
	@echo ""
	@echo "$(CYAN)Docker Commands:$(RESET)"
	@echo "  $(GREEN)make dev$(RESET)              Start all Docker services (frontend, backend, postgres, ollama)"
	@echo "  $(GREEN)make up$(RESET)               Alias for make dev"
	@echo "  $(GREEN)make stop$(RESET)             Stop all Docker services"
	@echo "  $(GREEN)make logs$(RESET)             Follow Docker container logs"
	@echo "  $(GREEN)make reset$(RESET)            Full reset: stop, remove volumes, rebuild and start"
	@echo "  $(GREEN)make reset-db$(RESET)         Reset database only (removes postgres volume)"
	@echo "  $(GREEN)make rebuild$(RESET)          Rebuild containers without cache"
	@echo "  $(GREEN)make shared$(RESET)           Start with Cloudflare Tunnel for external access"
	@echo ""
	@echo "$(CYAN)Dependency Management (Local IDE Support):$(RESET)"
	@echo "  $(GREEN)make install-deps$(RESET)     Install all dependencies (frontend + backend)"
	@echo "  $(GREEN)make install-frontend$(RESET) Install frontend dependencies (npm install)"
	@echo "  $(GREEN)make install-backend$(RESET)  Install backend dependencies (pip install)"
	@echo "  $(GREEN)make clean-deps$(RESET)       Remove dependency caches (node_modules, __pycache__)"
	@echo "  $(GREEN)make reinstall-frontend$(RESET) Clean and reinstall frontend dependencies"
	@echo "  $(GREEN)make reinstall-backend$(RESET)  Clean and reinstall backend dependencies"
	@echo "  $(GREEN)make reinstall-deps$(RESET)   Clean and reinstall all dependencies"
	@echo ""
	@echo "$(CYAN)Other:$(RESET)"
	@echo "  $(GREEN)make services$(RESET)         Scan and manage optional services (C++, Go, Rust)"
	@echo "  $(GREEN)make session$(RESET)          Start a logged development session"
	@echo ""
	@echo "$(YELLOW)Service URLs when running:$(RESET)"
	@echo "  Frontend:  http://localhost:5173"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  Ollama:    http://localhost:11435"
	@echo "  Postgres:  localhost:5432"
	@echo ""

# ============================================================
# Preflight Checks & Contract Enforcement
# ============================================================

check-ports:
	@echo "Checking port availability..."
	@# If containers are already running, we assume ports are fine (re-entrant safe)
	@if docker ps --format '{{.Names}}' | grep -q 'aequitas-backend'; then \
		echo "Containers running, skipping strict port validation."; \
	else \
		for port in 5432 11435 8000 5173; do \
			if lsof -i :$$port -t >/dev/null; then \
				echo "$(YELLOW)Port $$port is busy. Checking if it's Docker...$(RESET)"; \
				if ! docker ps --format '{{.Ports}}' | grep -q "$$port"; then \
					echo "$(RED)Error: Port $$port is in use by a non-Docker process.$(RESET)"; \
					exit 1; \
				fi; \
			fi; \
		done; \
	fi
	@echo "$(GREEN)Port checks passed.$(RESET)"

preflight: check-ports
	@echo "$(GREEN)Preflight checks passed.$(RESET)"

check-dev-running:
	@echo "Verifying dev stack..."
	@if ! docker network inspect aequitas-dev-net >/dev/null 2>&1; then \
		echo "$(RED)Error: Network 'aequitas-dev-net' not found.$(RESET)"; \
		echo "Shared mode requires dev stack running. Run 'make dev' first."; \
		exit 1; \
	fi
	@if ! docker ps --format '{{.Names}}' | grep -q 'aequitas-backend-dev'; then \
		echo "$(RED)Error: Backend container is not running.$(RESET)"; \
		exit 1; \
	fi
	@if ! docker ps --format '{{.Names}}' | grep -q 'aequitas-frontend-dev'; then \
		echo "$(RED)Error: Frontend container is not running.$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Dev stack verified.$(RESET)"

up: dev ## Alias for dev

dev: preflight ## Start all Docker services
	@echo "Starting Unified Dev Mode..."
	@echo "Starting Docker services (Postgres, Ollama, Backend, Frontend)"
	docker compose -f $(DOCKER_COMPOSE_DEV) up -d --build
	@echo "Unified Dev Mode is running."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "Ollama: http://localhost:11435"
	@echo "Postgres: localhost:5432"

metatheos-dev: ## Start Metatheos GUI (Tauri)
	@echo "Starting Metatheos GUI..."
	cd metatheos/metatheos-gui && cargo tauri dev

dev-all: ## Start Aequitas (Docker) and Metatheos (Tauri) concurrently
	@echo "Starting Aequitas + Metatheos..."
	@echo "NOTE: This runs 'make dev' in the background. Use 'make stop' to kill Docker services."
	make dev & \
	sleep 10 && \
	make metatheos-dev

stop:
	@echo "Stopping Unified Dev Mode..."
	@if [ -L "dev_sessions/latest" ]; then \
		echo "Saving Docker logs to current session..."; \
		docker compose -f $(DOCKER_COMPOSE_DEV) logs > dev_sessions/latest/docker_logs_final.txt 2>&1 || true; \
	fi
	@echo "Stopping Docker services..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down
	@echo "All services stopped."

reset-db:
	@echo "Resetting development database..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down -v
	docker compose -f $(DOCKER_COMPOSE_DEV) up -d postgres
	@echo "Database reset complete."

reset:
	@echo "Resetting all containers..."
	@echo "Stopping services..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down
	@echo "Removing containers, networks, and volumes..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down -v
	@echo "Recreating services..."
	docker compose -f $(DOCKER_COMPOSE_DEV) up -d --build
	@echo "Reset complete!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "Ollama: http://localhost:11435"
	@echo "Postgres: localhost:5432"

rebuild:
	@echo "Rebuilding containers without cache..."
	@echo "Stopping services..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down
	@echo "Rebuilding with --no-cache..."
	docker compose -f $(DOCKER_COMPOSE_DEV) build --no-cache
	@echo "Starting services..."
	docker compose -f $(DOCKER_COMPOSE_DEV) up -d
	@echo "Rebuild complete!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend: http://localhost:8000"
	@echo "Ollama: http://localhost:11435"
	@echo "Postgres: localhost:5432"

logs:
	@echo "Following Docker logs..."
	docker compose -f $(DOCKER_COMPOSE_DEV) logs -f

# ============================================================
# Dependency Management
# ============================================================

install-deps:
	@echo "Installing all dependencies..."
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && python3 -m pip install -r requirements.txt
	@echo "All dependencies installed!"

install-frontend:
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "Frontend dependencies installed!"

install-backend:
	@echo "Installing backend dependencies..."
	cd $(BACKEND_DIR) && python3 -m pip install -r requirements.txt
	@echo "Backend dependencies installed!"

clean-deps:
	@echo "Cleaning dependency caches..."
	@echo "Cleaning npm cache..."
	cd $(FRONTEND_DIR) && rm -rf node_modules package-lock.json
	@echo "Cleaning Python cache..."
	cd $(BACKEND_DIR) && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND_DIR) && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Dependency caches cleaned!"

reinstall-frontend:
	@echo "Reinstalling frontend dependencies..."
	cd $(FRONTEND_DIR) && rm -rf node_modules package-lock.json
	cd $(FRONTEND_DIR) && npm install
	@echo "Frontend dependencies reinstalled!"
	@echo "Tip: Run 'make rebuild' to rebuild containers with fresh dependencies"

reinstall-backend:
	@echo "Reinstalling backend dependencies..."
	cd $(BACKEND_DIR) && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND_DIR) && python3 -m pip install --force-reinstall -r requirements.txt
	@echo "Backend dependencies reinstalled!"
	@echo "Tip: Run 'make rebuild' to rebuild containers with fresh dependencies"

reinstall-deps: clean-deps install-deps
	@echo "All dependencies reinstalled!"
	@echo "Tip: Run 'make rebuild' to rebuild containers with fresh dependencies"

shared: check-dev-running
	@echo "Starting Shared Dev Mode..."
	@echo "Starting Docker services with Tunnel..."
	docker compose -f $(DOCKER_COMPOSE_DEV) -f docker-compose.shared.yml up -d --build
	@echo "Shared Dev Mode is running."
	@echo "To view the public URL, run: docker compose -f $(DOCKER_COMPOSE_DEV) -f docker-compose.shared.yml logs tunnel | grep 'trycloudflare.com'"



session: ## Start a logged development session
	@echo "Starting watched session..."
	@./scripts/maintenance/dev_session_logger.sh wrap

# Placeholder for optional services

services:
	@echo "Managing optional services..."
	@if [ -d "services" ]; then \
		for service_dir in services/*; do \
			if [ -f "$$service_dir/main.cpp" ]; then \
				echo "Found C++ service in $$service_dir"; \
				# Add compilation and run commands here \
			elif [ -f "$$service_dir/main.go" ]; then \
				echo "Found Go service in $$service_dir"; \
				# Add compilation and run commands here \
			elif [ -f "$$service_dir/main.rs" ]; then \
				echo "Found Rust service in $$service_dir"; \
				# Add compilation and run commands here \
			fi; \
		done; \
	else \
		echo "No 'services' directory found."; \
	fi

