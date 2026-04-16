set shell := ["bash", "-cu"]

backend_dir := "backend"
frontend_dir := "frontend"
backend_python := backend_dir / ".venv/bin/python"

# -------------------------
# Backend
# -------------------------

backend:
    {{backend_python}} {{backend_dir}}/manage.py runserver 127.0.0.1:8000

# -------------------------
# Frontend
# -------------------------

frontend:
    cd {{frontend_dir}} && pnpm dev --host

# -------------------------
# Combined (manual multi-term)
# -------------------------

dev:
    @echo "Run in two terminals:"
    @echo "just backend"
    @echo "just frontend"

# -------------------------
# Quick checks
# -------------------------

check-backend:
    {{backend_python}} {{backend_dir}}/manage.py check

migrate:
    {{backend_python}} {{backend_dir}}/manage.py migrate

shell:
    {{backend_python}} {{backend_dir}}/manage.py shell

# -------------------------
# Full dev environment (tmux)
# -------------------------

up:
    tmux new-session -d -s dev "{{backend_python}} {{backend_dir}}/manage.py runserver 127.0.0.1:8000"
    tmux split-window -h "cd frontend && pnpm dev --host"
    tmux select-layout even-horizontal
    tmux attach -t dev

down:
    tmux kill-session -t dev || true

logs:
    tmux capture-pane -pt dev:0
