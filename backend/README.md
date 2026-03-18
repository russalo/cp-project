# Backend setup (Django + PostgreSQL)

For full project onboarding, start with the repo root `README.md`.

This file focuses on the backend-specific pieces.

## Quick start

From the project root:

```bash
cd ~/Projects/cp-project
make setup-backend
```

If you also want frontend dependencies installed, use:

```bash
cd ~/Projects/cp-project
make setup
```

The setup script will:

- create `backend/.venv/` if missing
- install Python dependencies
- create `backend/.env` from `backend/.env.example` if missing
- install PostgreSQL packages on Fedora/Ubuntu unless skipped
- bootstrap the app PostgreSQL role/database when env values are present
- run Django checks and migrations

Note: the repository target is Python `3.12` to match CI/production. The script will warn if a different Python version is detected.

## 1) Install backend dependencies manually

```bash
cd ~/Projects/cp-project/backend
.venv/bin/pip install -r requirements.txt
```

## 2) Install PostgreSQL manually

Fedora (dev machine):

```bash
sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

Ubuntu 22.04 (VPS):

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

## 3) Create database and user manually

```bash
sudo -u postgres psql
```

Inside `psql`:

```sql
CREATE DATABASE cp_project;
CREATE USER cp_project_user WITH PASSWORD 'change-me';
ALTER ROLE cp_project_user SET client_encoding TO 'utf8';
ALTER ROLE cp_project_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cp_project_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cp_project TO cp_project_user;
\q
```

## 4) Configure environment variables

```bash
cd ~/Projects/cp-project/backend
cp .env.example .env
```

Then edit `.env` with real values.

The template includes local-development defaults (`cp_project`, `cp_project_user`, `change-me`) so `make setup` can bootstrap quickly on a fresh machine.
Update these values if your local PostgreSQL config is different.

The required database variables are:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Optional but commonly needed:

- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`

## 5) Verify Django is using PostgreSQL

```bash
cd ~/Projects/cp-project/backend
.venv/bin/python manage.py check --database default
.venv/bin/python manage.py migrate
.venv/bin/python manage.py shell -c "from django.db import connection; print(connection.vendor)"
```

Expected output from the last command: `postgresql`

## Run the backend during development

From the repo root:

```bash
make backend-run
```

`backend/config/settings.py` is now PostgreSQL-only and requires `DB_NAME`, `DB_USER`, and `DB_PASSWORD` to be set.
