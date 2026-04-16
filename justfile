set shell := ["bash", "-cu"]

backend_dir := "backend"
frontend_dir := "frontend"

# -------------------------
# Backend
# -------------------------

backend:
    cd {{backend_dir}} && source .venv/bin/activate && python manage.py runserver 127.0.0.1:8000

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
    cd {{backend_dir}} && source .venv/bin/activate && python manage.py check

migrate:
    cd {{backend_dir}} && source .venv/bin/activate && python manage.py migrate

shell:
    cd {{backend_dir}} && source .venv/bin/activate && python manage.py shell

# -------------------------
# Full dev environment (tmux)
# -------------------------

up:
    tmux new-session -d -s dev "cd backend && source .venv/bin/activate && python manage.py runserver 127.0.0.1:8000"
    tmux split-window -h "cd frontend && pnpm dev --host"
    tmux select-layout even-horizontal
    tmux attach -t dev

down:
    tmux kill-session -t dev || true

logs:
    tmux capture-pane -pt dev:0
