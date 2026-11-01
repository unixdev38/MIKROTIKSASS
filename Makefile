# ---------------------------------------------------------------------------
# Kora — raccourcis de développement (Linux / macOS / WSL / Git Bash)
# Windows : utilisez `dev.ps1` (PowerShell) ou `dev.bat` (cmd) — mêmes tâches.
# ---------------------------------------------------------------------------
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install install-console migrate test lint demo run console probe-router maquettes clean

help:
	@echo "make install     Crée le venv et installe les dépendances"
	@echo "make migrate     Applique les migrations"
	@echo "make test        Lance la suite de tests"
	@echo "make lint        Ruff + compilation Python"
	@echo "make demo        Parcours complet de démonstration (routeur simulé)"
	@echo "make console     Console React en développement sur 0.0.0.0:5173"
	@echo "make probe-router  Teste un routeur réel : HOST=… USER=… PASS=… [PORT=…] [HTTP=1]"
	@echo "make run         Serveur de développement sur 0.0.0.0:8001"
	@echo "make maquettes   Régénère et sert les maquettes sur :8000"

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e "backend[dev]"
	$(MAKE) install-console

migrate:
	cd backend && ../$(PY) manage.py makemigrations --check --dry-run || true
	cd backend && ../$(PY) manage.py migrate --noinput

test:
	cd backend && ../$(PY) -m pytest

install-console:
	cd frontend/console && npm install --no-audit --no-fund

console:
	cd frontend/console && npm run dev

probe-router:
	cd backend && ../$(PY) manage.py probe_router --host "$(HOST)" --username "$(USER)" \
		--password "$(PASS)" $(if $(PORT),--port $(PORT),) $(if $(HTTP),--http,)

lint:
	cd backend && ../$(PY) -m ruff check .
	cd backend && ../$(PY) -m compileall -q apps core config

demo:
	cd backend && ../$(PY) manage.py demo_smoke

run:
	cd backend && ../$(PY) manage.py runserver 0.0.0.0:8001

maquettes:
	$(PY) design/build.py
	$(PY) -m http.server 8000 --bind 0.0.0.0 -d design/dist

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -f backend/db.sqlite3
