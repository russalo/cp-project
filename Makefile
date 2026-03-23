SHELL := /bin/bash
ROOT_DIR := $(abspath .)
VENV_PYTHON := $(ROOT_DIR)/backend/.venv/bin/python
BACKEND_PYTHON := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(shell command -v python3 2>/dev/null || printf python3))

.PHONY: setup setup-online setup-backend deps-refresh db-check backend-check backend-test frontend-install frontend-build local-check dev-check backend-run frontend-dev continuity-status start-session stop-session docs-audit knowledge-pipeline-check inbox-status inbox-route-draft archive-audit assistant-doc-check

setup:
	./setup.sh

setup-online: setup

setup-backend:
	./setup.sh --skip-frontend

deps-refresh:
	@if [ ! -x "$(VENV_PYTHON)" ]; then \
		echo "backend/.venv is missing or not initialized. Run 'make setup-backend' (or './setup.sh --skip-frontend') first."; \
		exit 1; \
	fi
	cd backend && "$(VENV_PYTHON)" -m pip install -r requirements.txt
	cd frontend && npm ci

db-check:
	@cd backend && . .env && \
	if command -v pg_isready >/dev/null 2>&1; then \
		pg_isready -h "$${DB_HOST:-127.0.0.1}" -p "$${DB_PORT:-5432}" || \
		( echo "PostgreSQL is not responding at $${DB_HOST:-127.0.0.1}:$${DB_PORT:-5432}. Start PostgreSQL or fix backend/.env."; exit 1 ); \
	else \
		echo "pg_isready not found; skipping socket-level PostgreSQL readiness check."; \
	fi

backend-check:
	@if [ ! -f backend/.env ]; then \
		echo "backend/.env is missing. Run 'make setup-online' or copy backend/.env.example first."; \
		exit 1; \
	fi
	@$(MAKE) db-check
	cd backend && "$(BACKEND_PYTHON)" manage.py check
	cd backend && "$(BACKEND_PYTHON)" manage.py migrate --check

frontend-install:
	cd frontend && npm ci

frontend-build:
	cd frontend && npm ci && npm run lint && npm run build

dev-check:
	$(MAKE) backend-check
	$(MAKE) frontend-build

backend-test:
	cd backend && "$(BACKEND_PYTHON)" -m pytest

local-check:
	$(MAKE) backend-check
	$(MAKE) backend-test
	$(MAKE) frontend-build

backend-run:
	cd backend && "$(BACKEND_PYTHON)" manage.py runserver

frontend-dev:
	cd frontend && npm run dev

continuity-status:
	git --no-pager status --short --branch
	@echo
	@if git rev-parse --verify HEAD >/dev/null 2>&1; then \
		git --no-pager log --oneline -5; \
	else \
		echo "No commits yet on this clone."; \
	fi

docs-audit:
	"$(BACKEND_PYTHON)" scripts/docs_audit.py --write-report

knowledge-pipeline-check:
	"$(BACKEND_PYTHON)" scripts/knowledge_pipeline_check.py --write-report

inbox-status:
	"$(BACKEND_PYTHON)" scripts/inbox_status.py --write-report

inbox-route-draft:
	"$(BACKEND_PYTHON)" scripts/inbox_route_draft.py --write-report

archive-audit:
	"$(BACKEND_PYTHON)" scripts/archive_candidates.py --write-report

assistant-doc-check:
	"$(BACKEND_PYTHON)" scripts/assistant_doc_diff.py --write-report

start-session:
	@echo "[session] Syncing and verifying local environment"
	@if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "[session] WARNING: working tree is dirty — commit or stash before pulling."; \
		git --no-pager status --short; \
		exit 1; \
	fi
	@if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then \
		echo "[session] Syncing via GitHub CLI"; \
		gh repo sync --branch "$$(git rev-parse --abbrev-ref HEAD)" || git pull --rebase; \
	else \
		echo "[session] GitHub CLI unavailable or not authenticated; falling back to git pull --rebase"; \
		git pull --rebase; \
	fi
	$(MAKE) continuity-status
	$(MAKE) local-check
	"$(BACKEND_PYTHON)" scripts/docs_session_start.py

stop-session:
	@echo "[session] Preparing end-of-session checkpoint"
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" = "main" ]; then \
		echo "[session] ERROR: you are on main — create a feature/fix branch before committing."; \
		exit 1; \
	fi
	@echo "[session] Reminder: update DEV-SESSION.md and DECISIONS.md (if needed) before commit"
	$(MAKE) backend-check
	"$(BACKEND_PYTHON)" scripts/homework_rollover.py
	"$(BACKEND_PYTHON)" scripts/docs_session_stop.py
	git status
	git add -A
	@if git diff --cached --quiet; then \
		echo "[session] No staged changes to commit."; \
	else \
		branch="$$(git rev-parse --abbrev-ref HEAD)"; \
		git commit -m "$(if $(MSG),$(MSG),WIP: session checkpoint)"; \
		if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then \
			echo "[session] Configuring git auth via GitHub CLI"; \
			gh auth setup-git >/dev/null 2>&1 || true; \
		else \
			echo "[session] GitHub CLI unavailable or not authenticated; using existing git remote auth"; \
		fi; \
		if git push -u origin HEAD; then \
			echo "[session] Push succeeded."; \
		else \
			echo "[session] Push rejected. Attempting pull --rebase and one retry."; \
			git pull --rebase origin "$$branch" && git push -u origin HEAD; \
		fi; \
	fi
