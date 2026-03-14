SHELL := /bin/bash
ROOT_DIR := $(abspath .)
VENV_PYTHON := $(ROOT_DIR)/.venv/bin/python

.PHONY: setup setup-backend backend-check frontend-install frontend-build dev-check backend-run frontend-dev continuity-status

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
