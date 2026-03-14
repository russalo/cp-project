#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$ROOT_DIR/.venv"
TARGET_PYTHON_MINOR="3.12"
TARGET_NODE_MAJOR="22"

SKIP_FRONTEND=0
SKIP_POSTGRES_INSTALL=0
SKIP_DB_BOOTSTRAP=0

log() {
  echo "[setup] $*"
}

usage() {
  cat <<EOF
Usage: ./setup.sh [options]

Options:
  --skip-frontend         Skip npm install for the frontend
  --skip-postgres-install Skip automatic PostgreSQL package installation
  --skip-db-bootstrap     Skip PostgreSQL role/database bootstrap
  -h, --help              Show this help message
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

find_python() {
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  elif command -v python >/dev/null 2>&1; then
    echo "python"
  else
    echo "Missing required command: python3.12, python3, or python" >&2
    exit 1
  fi
}

warn_runtime_mismatch() {
  local python_bin="$1"
  local detected_python
  detected_python="$($python_bin -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

  if [[ "$detected_python" != "$TARGET_PYTHON_MINOR" ]]; then
    log "Warning: detected Python $detected_python, but repo target is $TARGET_PYTHON_MINOR to match CI/production"
  fi

  if command -v node >/dev/null 2>&1; then
    local detected_node
    detected_node="$(node --version | sed 's/^v//' | cut -d. -f1)"
    if [[ "$detected_node" != "$TARGET_NODE_MAJOR" ]]; then
      log "Warning: detected Node $detected_node, but repo target is $TARGET_NODE_MAJOR"
    fi
  fi
}

install_postgresql() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
  else
    echo "Cannot detect OS; /etc/os-release not found." >&2
    return
  fi

  case "${ID:-}" in
    fedora)
      log "Installing PostgreSQL on Fedora"
      sudo dnf install -y postgresql-server postgresql-contrib
      if [[ ! -f /var/lib/pgsql/data/PG_VERSION ]]; then
        sudo postgresql-setup --initdb
      fi
      sudo systemctl enable --now postgresql
      ;;
    ubuntu|debian)
      log "Installing PostgreSQL on Ubuntu/Debian"
      sudo apt update
      sudo apt install -y postgresql postgresql-contrib
      sudo systemctl enable --now postgresql
      ;;
    *)
      log "Unsupported distro for auto-install (${ID:-unknown}). Install PostgreSQL manually."
      ;;
  esac
}

bootstrap_db() {
  if [[ "$SKIP_DB_BOOTSTRAP" -eq 1 ]]; then
    log "Skipping DB bootstrap by request"
    return
  fi

  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    log "Skipping DB bootstrap: backend/.env not found"
    return
  fi

  set -a
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.env"
  set +a

  if [[ -z "${DB_NAME:-}" || -z "${DB_USER:-}" || -z "${DB_PASSWORD:-}" ]]; then
    log "Skipping DB bootstrap: DB_NAME/DB_USER/DB_PASSWORD must be set in backend/.env"
    return
  fi

  log "Creating PostgreSQL role/database if missing"
  sudo -u postgres psql -v db_name="$DB_NAME" -v db_user="$DB_USER" -v db_password="$DB_PASSWORD" <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'db_user') THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', :'db_user', :'db_password');
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name') THEN
    EXECUTE format('CREATE DATABASE %I OWNER %I', :'db_name', :'db_user');
  END IF;
END
$$;
SQL
}

install_frontend_dependencies() {
  if [[ "$SKIP_FRONTEND" -eq 1 ]]; then
    log "Skipping frontend dependency install by request"
    return
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "Missing required command: npm (install Node ${TARGET_NODE_MAJOR}.x or rerun with --skip-frontend)" >&2
    exit 1
  fi

  log "Installing frontend Node dependencies"
  (
    cd "$FRONTEND_DIR"
    npm ci
  )
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-frontend)
        SKIP_FRONTEND=1
        ;;
      --skip-postgres-install)
        SKIP_POSTGRES_INSTALL=1
        ;;
      --skip-db-bootstrap)
        SKIP_DB_BOOTSTRAP=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
    shift
  done
}

main() {
  local python_bin

  parse_args "$@"

  python_bin="$(find_python)"
  require_cmd sudo
  warn_runtime_mismatch "$python_bin"

  if [[ "$SKIP_POSTGRES_INSTALL" -eq 1 ]]; then
    log "Skipping PostgreSQL package install by request"
  else
    install_postgresql
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment"
    "$python_bin" -m venv "$VENV_DIR"
  fi

  log "Installing backend Python dependencies"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

  install_frontend_dependencies

  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    log "Creating backend/.env from backend/.env.example"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  fi

  bootstrap_db

  log "Running Django checks and migrations"
  (
    cd "$BACKEND_DIR"
    "$VENV_DIR/bin/python" manage.py check
    "$VENV_DIR/bin/python" manage.py migrate
  )

  log "Setup complete"
}

main "$@"
