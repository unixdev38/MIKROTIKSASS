# 17 · Travailler sous Windows (PowerShell)

> **But** : lancer tout le projet — API, console, tests, routeur VirtualBox — sur un poste
> Windows, **sans `make`**. Temps de mise en route : 10 minutes.

---

## 1. Prérequis

| Outil | Version | Vérification | Installation |
|---|---|---|---|
| Python | **3.11+** | `python --version` | [python.org](https://www.python.org/downloads/windows/) (cocher *Add Python to PATH*) |
| Node.js | **18+** (npm inclus) | `node --version` ; `npm --version` | [nodejs.org](https://nodejs.org/) |
| Git | récent | `git --version` | [git-scm.com](https://git-scm.com/download/win) |
| PowerShell | 5.1+ (fourni) | `$PSVersionTable.PSVersion` | déjà installé |

> Le lanceur `py -3` fonctionne aussi partout où ce document écrit `python` :
> `py -3 -m venv .venv`.

---

## 2. `make` n'est pas nécessaire

Le `Makefile` du dépôt n'est qu'un **raccourci Unix**. Son équivalent Windows est
`dev.ps1` (PowerShell) — et `dev.bat` si vous préférez `cmd.exe`.

```powershell
# À la racine du dépôt
.\dev.ps1 install      # .venv + dépendances Python + npm install
.\dev.ps1 migrate      # schéma de base
.\dev.ps1 demo         # données de démonstration (routeur simulé)
.\dev.ps1 test         # tests
.\dev.ps1 run          # API  → http://localhost:8001
.\dev.ps1 console      # UI   → http://localhost:5173   (dans une 2e fenêtre)
```

En `cmd.exe` : `dev.bat test`, `dev.bat run`, etc.

### Si PowerShell bloque le script

```
.\dev.ps1 : Impossible de charger le fichier … car l'exécution de scripts est désactivée
```

Trois solutions, de la plus douce à la plus large :

```powershell
# 1. Ponctuel (recommandé)
powershell -ExecutionPolicy Bypass -File .\dev.ps1 test

# 2. Pour la session courante seulement
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Définitif pour l'utilisateur (à faire en connaissance de cause)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## 3. Commandes équivalentes (sans script)

```powershell
# Environnement (dépendances figées, reproductibles)
python -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements-dev.txt
cd frontend\console; npm install; cd ..\..

# Variante « paquet éditable » (équivalente)
# .\.venv\Scripts\pip install -e "backend[dev]"

# Base de données et démonstration
cd backend
..\.venv\Scripts\python manage.py migrate
..\.venv\Scripts\python manage.py demo_smoke
cd ..

# Serveurs (deux fenêtres PowerShell)
cd backend; ..\.venv\Scripts\python manage.py runserver 0.0.0.0:8001
cd frontend\console; npm run dev

# Qualité
cd backend; ..\.venv\Scripts\python -m pytest
cd backend; ..\.venv\Scripts\python -m ruff check .
```

> Dans PowerShell, le chemin de l'interpréteur est `.\.venv\Scripts\python.exe`
> (et non `.venv/bin/python` comme sous Linux).

---

## 4. Configuration : le fichier `.env`

`config/settings.py` charge automatiquement, au démarrage :

1. `backend\.env`
2. `.env` (racine du dépôt)

Les variables déjà présentes dans l'environnement **ont priorité** : en CI ou Docker,
rien n'est écrasé.

```powershell
Copy-Item .env.example .env
notepad .env     # puis adapter SECRET_KEY, SECRET_ENCRYPTION_KEY, bases…
```

Sans `.env`, le projet démarre quand même : SQLite, routeurs simulés, Celery synchrone.

### Variables à la volée (PowerShell)

```powershell
$env:MIKROTIK_LIVE_HOST = "192.168.56.101"
$env:MIKROTIK_LIVE_USER = "kora"
$env:MIKROTIK_LIVE_PASSWORD = "motdepasse"
cd backend; ..\.venv\Scripts\python -m pytest -m live -v
```

`set VAR=valeur` (cmd) ou `$env:VAR="valeur"` (PowerShell) ne durent que le temps de la
fenêtre — d'où l'intérêt du `.env`.

---

## 5. Ton routeur x86 dans VirtualBox

Réseau : carte **« Accès par hôte »** → adaptateur `VirtualBox Host-Only Ethernet Adapter`,
adresse de l'hôte `192.168.56.1`, VM en `192.168.56.101/24` (voir `docs/15`).

```powershell
# Depuis le dépôt : test direct, sans base de données
.\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "motdepasse"

# Variante HTTP simple (service www, port 80)
.\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "…" -Http -RouterPort 80

# Avec les interfaces
.\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "…" -Interfaces

# Ou en appel direct
cd backend
..\.venv\Scripts\python manage.py probe_router --host 192.168.56.101 --username kora --password "…"
```

Vérification réseau préalable :

```powershell
ping 192.168.56.101
Test-NetConnection 192.168.56.101 -Port 443
```

Puis dans la console : **Routeurs → Ajouter** (`192.168.56.101`, port 443, HTTPS) →
**Connecter le routeur** → **Tester la connexion**.

---

## 6. Pièges classiques sous Windows

| Symptôme | Cause | Solution |
|---|---|---|
| `python : terme non reconnu` | Python absent du PATH | réinstaller en cochant *Add to PATH*, ou utiliser `py -3` |
| `ModuleNotFoundError: rest_framework_simplejwt` | installation incomplète (ancien `pip install -e`) | `.\.venv\Scripts\pip install -r backend\requirements-dev.txt` |
| `Impossible de charger … dev.ps1` | politique d'exécution | voir §2 |
| `npm : terme non reconnu` | Node.js absent | installer Node 18+, **rouvrir** le terminal |
| `make : commande introuvable` | normal sous Windows | utiliser `dev.ps1` / `dev.bat` |
| `curl` renvoie autre chose | sous PowerShell 5, `curl` est un alias de `Invoke-WebRequest` | utiliser `curl.exe` |
| `Port 8001 déjà utilisé` | serveur précédent encore actif | `Get-NetTCPConnection -LocalPort 8001` puis `Stop-Process -Id <pid>` |
| Accents illisibles dans la console | page de code | `chcp 65001` |
| `pytest` ne trouve pas `config.settings` | lancé hors de `backend\` | `cd backend` d'abord (ou `.\dev.ps1 test`) |
| Le routeur répond mais `403` | policy `rest-api` manquante | `/user group set kora policy=read,write,api,rest-api,test` |

---

## 7. Ce qui est identique aux autres systèmes

- Le code, les migrations et les tests : aucun chemin absolu, aucun `/` codé en dur.
- La console : `npm run dev`, proxy `/api` → `127.0.0.1:8001` (aucune configuration CORS).
- Les maquettes statiques : `python design\build.py` puis
  `python -m http.server 8000 -d design\dist`.
