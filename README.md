# MIKROTIKSASS

**SaaS de gestion de parc MikroTik** — hotspot Wi-Fi payant, abonnés PPPoE, caisse, paiements
mobile money, supervision — construit avec **Django** + **React**.

> **État du projet : socle opérationnel (API + console) et connecteur MikroTik réel.**
> Le dépôt contient le **dossier de conception complet** (vision, architecture, intégration RouterOS,
> données, API, frontend, sécurité, infra, roadmap, ADR, maquettes) **et** le début du backend Django :
> multi-tenant, rôles, parc de routeurs, enrôlement et sonde.
>
> ```bash
> make install && make migrate && make demo   # données de démonstration (routeur simulé)
> make run                                     # API   → http://localhost:8001
> make console                                 # UI    → http://localhost:5173
> make test                                    # 42 tests + 1 test « vrai routeur » optionnel
> ```

## Ce qui fonctionne déjà

| Fonction | État |
|---|---|
| Multi-tenant, rôles, isolation testée | ✅ |
| Authentification JWT (accès 15 min, refresh 7 j, rotation, révocation) | ✅ |
| Enregistrement d'un routeur + enrôlement (script RouterOS, secrets chiffrés AES-GCM) | ✅ |
| **Connexion à un vrai routeur RouterOS 7** (REST, HTTP/HTTPS, port libre) | ✅ |
| Sonde de connexion + persistance de la santé et des interfaces | ✅ |
| Workers Celery (sonde à la demande, par tenant) | ✅ |
| **Console React** (connexion, tableau de bord, routeurs, fiche, réglages) | ✅ |
| API binaire 8729 (RouterOS 6.49) | ⬜ P3 |
| Vouchers, RADIUS, caisse, paiements | ⬜ (P4–P6) |

> Tu as un routeur x86 dans VirtualBox ? Le guide complet est ici :
> [**docs/15 — Tester avec un routeur x86 dans VirtualBox**](docs/15-routeur-de-test-virtualbox.md).

---

## Le produit en une phrase

> « Gérez vos routeurs MikroTik, vos abonnés et vos encaissements depuis un navigateur,
> sans WinBox, sans Excel et sans être sur place. »

Trois briques :

1. **Plan de contrôle** (notre SaaS) : configurer les routeurs, gérer forfaits, vouchers, abonnés,
   factures — via l'API RouterOS, à travers un tunnel WireGuard que le routeur initie.
2. **Plan AAA** : FreeRADIUS authentifie les clients et remonte la consommation en temps réel ;
   le routeur reste autonome (utilisateurs locaux) si la plateforme tombe.
3. **Plan utilisateur** : le trafic Internet des clients finaux ne traverse **jamais** notre plateforme
   (ni proxy, ni filtrage, ni coût de bande passante).

```mermaid
flowchart LR
    OP["Opérateur / FAI"] --> CONSOLE["Console React"]
    CONSOLE --> API["API Django + DRF"]
    CLI["Client final"] --> PORTAL["Portail captif"] --> API
    API --> RADIUS["FreeRADIUS / AAA"]
    API --> PAY["Mobile money"]
    R["Routeurs MikroTik<br/>(client)"] <-->|"WireGuard + API 8729/REST"| API
    R -.->|"RADIUS 1812/1813"| RADIUS
```

---

## Ordre de lecture recommandé

| # | Document | Ce que vous y trouvez | Temps |
|---|---|---|---|
| 0 | [**Vision et produit**](docs/00-vision-et-produit.md) | Les 4 produits possibles, le choix recommandé, personas, périmètre MVP, prix, concurrence | 20 min |
| 1 | [**Architecture**](docs/01-architecture.md) | Diagrammes, composants, stack, flux détaillés, multi-tenant, exigences non fonctionnelles | 25 min |
| 2 | [**Intégration MikroTik**](docs/02-integration-mikrotik.md) | Protocole API, scripts routeur, RADIUS, pièges, compatibilité, sécurité, plan de validation | 35 min |
| 3 | [**Modèle de données**](docs/03-modele-donnees.md) | ERD, tables, index, rétention, chiffrement, tables RADIUS | 25 min |
| 4 | [**Contrat d'API**](docs/04-contrat-api.md) | Conventions REST, endpoints, erreurs, webhooks, temps réel | 20 min |
| 5 | [**Frontend React**](docs/05-frontend-react.md) | Stack, routes, état, temps réel, UX des parcours, performance 3G, tests | 15 min |
| 6 | [**Sécurité et exploitation**](docs/06-securite-exploitation.md) | Risques, contrôles, données personnelles, sauvegardes, runbooks | 20 min |
| 7 | [**Infrastructure**](docs/07-infrastructure-devops.md) | Environnements, arborescence, dev local avec CHR, prod, CI/CD, coûts | 20 min |
| 8 | [**Feuille de route**](docs/08-roadmap-budget.md) | Phases, backlog, budget en FCFA, mise sur le marché, risques | 15 min |
| 9 | [**Décisions d'architecture (ADR)**](docs/09-adr/) | 6 décisions argumentées (monolithe, REST/binaire, multi-tenant, RADIUS, WireGuard, SPA) | 15 min |
| 10 | [**Checklists**](docs/10-checklists.md) | Ce qu'il faut faire **avant** de coder, décisions ouvertes, durcissement, go-live | 15 min |
| 11 | [**Glossaire**](docs/11-glossaire.md) | Vocabulaire partagé réseau / RADIUS / produit | 10 min |
| 12 | [**Design system & maquettes**](docs/12-design-system.md) | Jetons, composants, spécification des 13 écrans, règles d'accessibilité | 15 min |
| 13 | [**Roadmap A → Z**](docs/13-roadmap-complet.md) | 10 phases, tâches numérotées, portes de sortie, sprints, définition de « ça marche » | 20 min |
| 14 | [**Conventions de code**](docs/14-conventions-de-code.md) | Couches, tailles maximales, docstrings, héritage, checklist de revue | 12 min |
| 15 | [**Routeur de test VirtualBox**](docs/15-routeur-de-test-virtualbox.md) | Brancher un RouterOS x86 local : réseau, API REST, CLI, console, dépannage | 12 min |

**Maquettes cliquables** : `design/dist/index.html` — prototype HTML/CSS sans dépendance
(13 écrans : console, caisse, enrôlement, portail captif, design system).

**Si vous ne lisez qu'un document** : `docs/00-vision-et-produit.md` (le quoi et le pourquoi),
puis `docs/10-checklists.md` (les 40 actions concrètes avant la première ligne de code).

---

## Stack retenue

| Couche | Choix |
|---|---|
| Backend | Django 5.2 LTS + Django REST Framework, Celery, Channels |
| Base | PostgreSQL 16 + TimescaleDB, Redis 7 |
| AAA | FreeRADIUS 3.2 (module Python vers notre base) |
| Routeurs | `librouteros` (API binaire) + `httpx` (REST), derrière une interface unique |
| Frontend | React 19 + TypeScript + Vite, TanStack Query, Tailwind + shadcn/ui |
| Exécution | Docker Compose sur un VPS, Traefik, GitHub Actions |
| Paiement | Agrégateur mobile money (Orange Money, Moov, Wave, Coris) |

---

## Arborescence cible (après la phase de code)

```
backend/     API Django, workers Celery, connecteur MikroTik   (présent)
design/      maquettes statiques + design system                (présent)
docs/        cette documentation                                (présent)
frontend/    console React + portail captif                     (à venir, P2/P3)
infra/       docker-compose, Traefik, FreeRADIUS, scripts .rsc   (à venir, P1/P8)
```

Dans `backend/` : `config/` (réglages uniques), `core/` (briques transverses),
`apps/{tenants,accounts,network,mikrotik,api}/`, `tests/`. Détail et démarrage rapide dans
[`backend/README.md`](backend/README.md).

Détail dans [`docs/07-infrastructure-devops.md`](docs/07-infrastructure-devops.md) §2.

---

## Voir les maquettes

```bash
python3 design/build.py                          # régénère design/dist/
python3 -m http.server 8000 -d design/dist       # puis http://localhost:8000
```

Point d'entrée : `index.html` (couverture cliquable). Tout est statique, sans CDN ni police distante,
donc consultable hors ligne et sur une connexion faible.

## Prochaines étapes immédiates (2 à 4 semaines)

1. **Valider le besoin** : 10 entretiens clients (cybercafés, hôtels, petits FAI, installateurs).
2. **Valider la technique** : monter 3 CHR + FreeRADIUS, tester `listen`, WireGuard derrière NAT,
   et **surtout** le comportement quand RADIUS est arrêté
   (voir [`docs/02-integration-mikrotik.md`](docs/02-integration-mikrotik.md) §11).
3. **Trancher les 10 décisions** listées dans [`docs/10-checklists.md`](docs/10-checklists.md) §2.
4. **Ouvrir le compte de paiement** (délai de validation 4 à 8 semaines : à lancer tout de suite).
5. **Faire tester les maquettes** à 5 utilisateurs réels (caissier, technicien, gérant, client final)
   et corriger avant de coder l'interface.
6. Alors seulement : **Phase 1 — socle** (multi-tenant, auth, parc réseau, enrôlement).

---

## Avertissements

- Les prix, coûts et volumes indiqués sont des **hypothèses de travail**, pas des engagements.
- Les aspects juridiques (protection des données, régulation télécom, fiscalité) doivent être
  **validés par un professionnel local** ; les documents de ce dépôt ne constituent pas un avis juridique.
- Aucun engagement de SLA ne doit être pris avant validation du comportement de repli RADIUS.

---

## Licence

À définir avant l'ouverture du dépôt (recommandation : propriétaire, tous droits réservés).
