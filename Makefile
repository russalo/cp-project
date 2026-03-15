SHELL := /bin/bash
ROOT_DIR := $(abspath .)
VENV_PYTHON := $(ROOT_DIR)/backend/.venv/bin/python

.PHONY: setup setup-backend backend-check frontend-install frontend-build dev-check backend-run frontend-dev continuity-status start-session stop-session decisions-sync decisions-sync-github milestones-sync

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

start-session:
	@echo "[session] Syncing and verifying local environment"
	git pull --rebase
	$(MAKE) continuity-status
	$(MAKE) dev-check

stop-session:
	@echo "[session] Preparing end-of-session checkpoint"
	@echo "[session] Reminder: update DEV-SESSION.md and DECISIONS.md (if needed) before commit"
	git status
	git add -A
	@if git diff --cached --quiet; then \
		echo "[session] No staged changes to commit."; \
	else \
		branch="$$(git rev-parse --abbrev-ref HEAD)"; \
		if [ "$$branch" = "main" ]; then \
			checkpoint_branch="checkpoint/$$(date +%Y%m%d-%H%M%S)"; \
			echo "[session] main is protected; creating $$checkpoint_branch for checkpoint commit"; \
			git checkout -b "$$checkpoint_branch"; \
			branch="$$checkpoint_branch"; \
		fi; \
		git commit -m "$(if $(MSG),$(MSG),WIP: session checkpoint)"; \
		git push -u origin "$$branch"; \
		remote_url="$$(git remote get-url origin)"; \
		repo_path="$$(echo "$$remote_url" | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$$##')"; \
		echo "[session] Open PR: https://github.com/$$repo_path/pull/new/$$branch"; \
	fi

decisions-sync:
	python3 scripts/sync_decisions.py --decisions-file DECISIONS.md --todo-file DECISIONS-TODO.md

decisions-sync-github:
	python3 scripts/sync_decisions.py --decisions-file DECISIONS.md --todo-file DECISIONS-TODO.md --sync-github

milestones-sync:
	python3 scripts/sync_milestones.py --milestones-file MILESTONES.md --todo-file MILESTONES-TODO.md

