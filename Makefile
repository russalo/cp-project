SHELL := /bin/bash
ROOT_DIR := $(abspath .)
VENV_PYTHON := $(ROOT_DIR)/backend/.venv/bin/python

.PHONY: setup setup-backend backend-check frontend-install frontend-build dev-check backend-run frontend-dev continuity-status start-session stop-session

setup:
	./setup.sh

setup-backend:
	./setup.sh --skip-frontend

backend-check:
	@if [ ! -f backend/.env ]; then \
		echo "backend/.env is missing. Run 'make setup' or copy backend/.env.example first."; \
		exit 1; \
	fi
	cd backend && "$(VENV_PYTHON)" manage.py check
	cd backend && "$(VENV_PYTHON)" manage.py migrate --check

frontend-install:
	cd frontend && npm ci

frontend-build:
	cd frontend && npm ci && npm run lint && npm run build

dev-check:
	$(MAKE) backend-check
	$(MAKE) frontend-build

backend-run:
	cd backend && "$(VENV_PYTHON)" manage.py runserver

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

start-session:
	@echo "[session] Syncing and verifying local environment"
	@if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "[session] WARNING: working tree is dirty — commit or stash before pulling."; \
		git --no-pager status --short; \
		exit 1; \
	fi
	git pull --rebase
	$(MAKE) continuity-status
	$(MAKE) dev-check
	cd backend && "$(VENV_PYTHON)" -m pytest

stop-session:
	@echo "[session] Preparing end-of-session checkpoint"
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" = "main" ]; then \
		echo "[session] ERROR: you are on main — create a feature/fix branch before committing."; \
		exit 1; \
	fi
	@echo "[session] Reminder: update DEV-SESSION.md and DECISIONS.md (if needed) before commit"
	$(MAKE) backend-check
	python3 scripts/homework_rollover.py
	git status
	git add -A
	@if git diff --cached --quiet; then \
		echo "[session] No staged changes to commit."; \
	else \
		git commit -m "$(if $(MSG),$(MSG),WIP: session checkpoint)"; \
		git push -u origin HEAD; \
	fi

