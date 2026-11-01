# Backend — Django

API et workers du SaaS. **Les règles de code sont dans [`docs/14-conventions-de-code.md`](../docs/14-conventions-de-code.md)** :
aucune logique dans les vues, tout passe par un service.

## Démarrage

```bash
make install     # venv + dépendances
make migrate     # schéma SQLite (ou Postgres via .env)
make demo        # parcours complet : tenant → site → routeur → enrôlement → sonde
make test        # suite de tests
make run         # http://localhost:8001
```

## Organisation

```
config/            réglages (unique), URLs, Celery, WSGI/ASGI
core/              briques transverses (modèles abstraits, contexte tenant, chiffrement, erreurs)
  api/             pagination, permissions, handler d'erreurs, vues de base
apps/tenants/      espaces de travail
apps/accounts/     utilisateurs, appartenances, rôles
apps/network/      sites, routeurs, identifiants, enrôlement, sondes, workers
apps/mikrotik/     connecteur RouterOS : schémas, backends (fake/rest/binaire), service
apps/api/          sérialiseurs et vues HTTP (fines)
tests/             tests d'isolation, d'enrôlement, de connecteur, d'API
```

## Couches (rappel)

```
vue (10-20 lignes) → serializer (forme) → service (métier + transaction) → selector/modèle
                                            ↘ task Celery (worker)
                                            ↘ backend MikroTik (I/O)
```

## Ce qui fonctionne aujourd'hui

| Fonction | État |
|---|---|
| Multi-tenant + rôles + isolation testée | ✅ |
| Enregistrement d'un routeur | ✅ |
| Enrôlement : secrets chiffrés + script RouterOS | ✅ |
| Sonde de connexion (backend factice) | ✅ |
| Workers de sonde (Celery) | ✅ |
| Backend REST réel | ⬜ P3 |
| Backend binaire (8729) | ⬜ P3 |
| Vouchers, RADIUS, paiements | ⬜ P4–P6 |

## Variables d'environnement

Voir [`.env.example`](../.env.example). En développement, aucun réglage n'est nécessaire :
SQLite, routeurs simulés et Celery en mode synchrone sont les valeurs par défaut.

## Sécurité

- `SECRET_ENCRYPTION_KEY` est **obligatoire** en production (clé base64 de 32 octets).
- Les secrets de management ne sont jamais renvoyés par l'API ni journalisés.
- Toute erreur métier devient une réponse `application/problem+json` avec un code stable.
