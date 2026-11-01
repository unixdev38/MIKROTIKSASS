# Backend — Django

API et workers du SaaS. **Les règles de code sont dans [`docs/14-conventions-de-code.md`](../docs/14-conventions-de-code.md)** :
aucune logique dans les vues, tout passe par un service.

## Démarrage

**Linux / macOS / WSL / Git Bash**

```bash
make install     # venv + dépendances (Django, DRF, JWT, Celery) + console
make migrate     # schéma SQLite (ou Postgres via .env)
make demo        # jeu de démonstration : tenant → site → routeur → enrôlement → sonde
make test        # suite de tests (79 + 1 test routeur réel optionnel)
make run         # API   → http://localhost:8001
make console     # UI    → http://localhost:5173
```

**Windows (PowerShell)** — aucun `make` nécessaire

```powershell
.\dev.ps1 install
.\dev.ps1 migrate
.\dev.ps1 demo
.\dev.ps1 test
.\dev.ps1 run        # API  → http://localhost:8001
.\dev.ps1 console    # UI   → http://localhost:5173
```

Détails : [`docs/17-environnement-windows.md`](../docs/17-environnement-windows.md).

Le fichier `.env` (racine ou `backend/`) est **chargé automatiquement** au démarrage ;
les variables du shell restent prioritaires.

## Dépendances

| Fichier | Contenu | Usage |
|---|---|---|
| `requirements.txt` | exécution, **versions figées** (Django, DRF + JWT, Celery, Redis, cryptography) | serveur, image Docker |
| `requirements-dev.txt` | `-r requirements.txt` + pytest, pytest-django, ruff | poste de développement |
| `pyproject.toml` | source de vérité (contraintes larges) + configuration pytest/ruff | publication, outillage |

```bash
# Installation reproductible (sans installation du paquet)
pip install -r backend/requirements-dev.txt

# ou, si vous préférez le paquet éditable
pip install -e "backend[dev]"
```

Un test (`tests/test_dependencies.py`) vérifie que **tout module importé est déclaré** et que
`pyproject.toml` / `requirements*.txt` restent alignés : un oubli de dépendance casse la CI,
plus la production.

## Organisation

```
config/            réglages (unique), URLs, Celery, WSGI/ASGI
core/              briques transverses (modèles abstraits, contexte tenant, chiffrement, erreurs)
  api/             pagination, permissions, handler d'erreurs, vues de base
apps/tenants/      espaces de travail
apps/accounts/     utilisateurs, appartenances, rôles
apps/network/      sites, routeurs, identifiants, enrôlement, sondes, workers
apps/mikrotik/     connecteur RouterOS : schémas, backends (fake/rest/binaire), service
apps/hotspot/      forfaits, lots de vouchers, provisioning RouterOS, quotas, export CSV
apps/api/          sérialiseurs, vues HTTP (fines), authentification JWT
tests/             tests d'isolation, d'enrôlement, de connecteur, d'API
```

## Couches (rappel)

```
vue (10-20 lignes) → serializer (forme) → service (métier + transaction) → selector/modèle
                                            ↘ task Celery (worker)
                                            ↘ backend MikroTik (I/O)
```

## Authentification

| Méthode | Endpoint | Corps |
|---|---|---|
| `POST` | `/api/v1/auth/token/` | `{"email", "password"}` → `access`, `refresh`, `tenant`, `role`, `tenants` |
| `POST` | `/api/v1/auth/refresh/` | `{"refresh"}` → nouveaux jetons (rotation) |
| `POST` | `/api/v1/auth/logout/` | `{"refresh"}` + `Authorization: Bearer …` → révocation |

Le jeton ne porte aucun droit : l'espace (`X-Tenant-Slug`) et le rôle sont vérifiés à
chaque requête. Durées : accès 15 min, refresh 7 jours (`JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`).

## Routeur réel (VM VirtualBox, CHR, hAP)

```bash
# Linux / macOS
python manage.py probe_router --host 192.168.56.101 --username kora --password '…'
MIKROTIK_LIVE_HOST=192.168.56.101 MIKROTIK_LIVE_USER=kora MIKROTIK_LIVE_PASSWORD='…' pytest -m live
```

```powershell
# Windows
cd backend
..\.venv\Scripts\python manage.py probe_router --host 192.168.56.101 --username kora --password "…"
$env:MIKROTIK_LIVE_HOST = "192.168.56.101"
..\.venv\Scripts\python -m pytest -m live -v
```

Guide détaillé (réseau VirtualBox, configuration RouterOS, dépannage) :
[`docs/15-routeur-de-test-virtualbox.md`](../docs/15-routeur-de-test-virtualbox.md).

## Ce qui fonctionne aujourd'hui

| Fonction | État |
|---|---|
| Multi-tenant + rôles + isolation testée | ✅ |
| Enregistrement d'un routeur | ✅ |
| Enrôlement : secrets chiffrés + script RouterOS | ✅ |
| Sonde de connexion (backend factice) | ✅ |
| Workers de sonde (Celery) | ✅ |
| Authentification JWT (rotation + révocation) | ✅ |
| Routeur RouterOS 7 réel (REST, HTTP/HTTPS, port libre) | ✅ |
| Console React branchée sur l'API | ✅ |
| Forfaits + lots de vouchers + envoi routeur + sync quotas + CSV | ✅ |
| Backend binaire (8729) | ⬜ P3 |
| Vouchers, RADIUS, paiements | ⬜ P4–P6 |

## Variables d'environnement

Voir [`.env.example`](../.env.example). En développement, aucun réglage n'est nécessaire :
SQLite, routeurs simulés et Celery en mode synchrone sont les valeurs par défaut.

## Sécurité

- `SECRET_ENCRYPTION_KEY` est **obligatoire** en production (clé base64 de 32 octets).
- Les secrets de management ne sont jamais renvoyés par l'API ni journalisés.
- Toute erreur métier devient une réponse `application/problem+json` avec un code stable.
