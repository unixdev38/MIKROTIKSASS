# 05 — Architecture frontend (React)

> Statut : **spécification** · Dernière mise à jour : 2026-11-01
> Cible : React 20 (ou 19) + TypeScript + Vite. Contrainte forte : **utilisable en 3G, sur tablette,
> en français**, par un caissier non technicien.

---

## 1. Principes

| # | Principe | Traduction |
|---|---|---|
| F1 | **Deux applications, pas trois** | `console` (opérateurs) et `portal` (clients finaux). Pas de micro-frontends. |
| F2 | **Le serveur est la source de vérité** | Pas de logique métier critique côté client (prix, quotas, permissions) |
| F3 | **Chargement perçu** | Squelettes, cache optimiste, données préchargées sur survol |
| F4 | **Débit avant tout** | < 250 Ko gzip hors graphiques, polices système, images WebP, lazy par route |
| F5 | **Erreurs visibles et actionnables** | Chaque erreur API devient un message en français avec une action proposée |
| F6 | **Hors-ligne toléré** | File d'attente des actions non critiques, bannière « connexion perdue » |
| F7 | **Accessibilité AA** | Navigation clavier, contrastes, libellés de formulaires |

---

## 2. Stack

| Brique | Choix | Pourquoi |
|---|---|---|
| Build | Vite | Démarrage instantané, build compact |
| Langage | TypeScript strict | Sécurité de typage, refactoring serein |
| Routage | React Router 7 (data router) | Loaders, erreurs par route, code splitting |
| Données serveur | TanStack Query v5 | Cache, retry, invalidation ciblée — remplace 80 % d'un store global |
| État global | Zustand (léger) | Seulement UI (sidebar, thème, tenant actif) |
| Formulaires | React Hook Form + Zod | Validation, messages d'erreur uniformes |
| UI | Tailwind CSS 4 + shadcn/ui (Radix) | Composants accessibles, thème par tenant via CSS variables |
| Tableaux | TanStack Table | Tri/filtres/pagination serveur, colonnes configurables |
| Graphiques | Recharts (dashboards) + uPlot (séries longues) | Poids maîtrisé |
| Temps réel | WebSocket natif + repli polling | Pas de librairie lourde |
| i18n | i18next + `react-i18next` | FR par défaut, EN prêt |
| Dates/monnaie | `date-fns-tz` + `Intl.NumberFormat('fr-BF', XOF)` | Fuseau Ouagadougou, FCFA sans décimales |
| Tests | Vitest + Testing Library + Playwright | Unitaires et parcours critiques |
| Qualité | ESLint, Prettier, `tsc --noEmit` | Bloquants en CI |

---

## 3. Applications et routes

### 3.1 Console (`apps/console`)

```
/                       → redirection selon l'état (login ou dashboard)
/login                  → connexion, MFA
/register               → création d'espace (essai)
/onboarding             → assistant : profil → premier routeur → premier forfait
/dashboard              → CA du jour, sessions actives, routeurs, alertes
/sites                  → liste / création / détail
/devices                → inventaire, statut, version, santé
/devices/:id            → onglets : Vue d'ensemble · Interfaces · Sessions · Config · Événements · Réglages
/devices/:id/enroll     → script d'enrôlement (copier, QR, PDF)
/plans                  → forfaits
/vouchers               → lots, codes, impression, recherche d'un code
/vouchers/batches/new   → générateur (quantité, préfixe, aperçu)
/subscribers            → clients récurrents (PPPoE)
/subscribers/:id        → abonnement, factures, sessions, historique
/billing                → factures, paiements, relances
/cashier                → caisse rapide (vendre un voucher en 3 clics)
/network/sessions       → sessions actives temps réel, déconnexion
/network/alerts         → alertes
/reports                → CA, consommation, top clients, export CSV/PDF
/settings               → espace de travail, membres, marque blanche, API, webhooks
/settings/audit         → journal d'audit
```

### 3.2 Portail (`apps/portal`) — rendu côté serveur ou statique + API
`/p/:tenantSlug` (page d'accueil personnalisée), `/p/:tenantSlug/buy`, `/p/:tenantSlug/status`,
`/p/:tenantSlug/help`. Servi sur le domaine du tenant si marque blanche.

### 3.3 Séparation et partage
`packages/ui` (composants), `packages/api-client` (types générés depuis OpenAPI), `packages/i18n`,
`packages/config`. Un monorepo pnpm + Turborepo, mais **un seul déploiement** par application.

---

## 4. Structure de dossiers (console)

```
apps/console/src/
  app/                 # providers, router, layout, guards
  features/
    auth/              # login, mfa, session
    dashboard/
    devices/           # liste, détail, enrôlement, actions
    plans/
    vouchers/
    subscribers/
    billing/
    sessions/
    alerts/
    reports/
    settings/
  components/
    ui/                # shadcn générés
    layout/            # sidebar, topbar, breadcrumbs
    data/              # DataTable, Filters, EmptyState, Pagination
    feedback/          # Toast, ErrorState, ConfirmDialog
  lib/                 # http, queryClient, dates, format, permissions
  hooks/               # usePermission, useTenant, useRealtime
  styles/
```

**Règle** : une *feature* ne dépend jamais d'une autre *feature* ; le partage passe par
`components/` ou `lib/`. Cela évite l'enchevêtrement après six mois.

---

## 5. Couche données

```ts
// packages/api-client/src/client.ts (esquisse)
export const api = createClient({
  baseUrl: import.meta.env.VITE_API_URL,
  getToken: () => authStore.getState().accessToken,
  onUnauthorized: async () => refreshSession(),
  onError: (problem) => toast.fromProblem(problem),   // message FR + action
  timeoutMs: 15_000,
});
```

- Types **générés** depuis OpenAPI (`openapi-typescript`) : aucune interface écrite à la main.
- Un hook par ressource : `useDevices()`, `useDevice(id)`, `useEnrollDevice()`.
- Clés de cache structurées : `['devices', {siteId}]`, `['device', id]`, `['sessions', 'active']`.
- Invalidation ciblée après mutation ; `staleTime` 30 s (60 s sur les listes de référence).
- Mutations optimistes uniquement sur les actions réversibles (renommage, activation).
- `refetchInterval` uniquement quand l'écran est visible (économie de données mobiles).

---

## 6. Expérience temps réel

| Écran | Stratégie | Fréquence |
|---|---|---|
| Sessions actives | WebSocket `sessions.active` + poll 30 s de secours | 10 s |
| Statut des routeurs | WebSocket `devices.status` | événementiel |
| Paiement en cours | WebSocket `payment.status` (sinon poll 3 s, plafonné 2 min) | événementiel |
| Graphiques de trafic | requête REST agrégée | 60 s |

Comportement obligatoire : reconnexion avec backoff, état « reconnexion… » visible, données
marquées comme périmées au-delà de 3× l'intervalle (grisées, pas supprimées).

---

## 7. UX des parcours critiques

### Vendre un voucher (caissier)
`/cashier` → montant ou forfait → numéro (optionnel) → **Encaisser** → le code s'affiche en grand +
QR, bouton « Imprimer » → journal du jour se met à jour. **≤ 3 clics, ≤ 5 s, clavier possible.**

### Enrôler un routeur (technicien)
Assistant en 4 étapes : site → modèle/version → script (copier le bloc, QR vers la doc) → attente de
connexion avec animation d'état → test de connexion réussi. Chaque échec propose une cause probable
(pare-feu, version trop ancienne, tunnel bloqué) et un lien vers la procédure.

### Comprendre une panne
Bannière rouge en haut : « 3 routeurs ne répondent plus » → clic → liste filtrable → fiche routeur
avec dernière erreur API, dernier heartbeat, uptime avant coupure, et bouton « Relancer le test ».

---

## 8. Performance et connexions faibles

- Budget : < 250 Ko gzip (JS initial), LCP < 2,5 s sur 3G simulée, CLS < 0,1.
- Pas de librairie de composants monolithique ; icônes en SVG inline optimisés.
- Graphiques chargés en `import()` différé.
- `Cache-Control: immutable` sur les assets hashés, service worker (PWA) pour la coquille.
- Pagination par curseur, jamais de « charger 10 000 lignes » dans le navigateur.
- Export CSV/PDF généré **côté serveur**, lien de téléchargement (pas de génération lourde en JS).
- Images de portail optimisées et servies par un CDN.

---

## 9. Sécurité frontend

| Risque | Contrôle |
|---|---|
| XSS | Pas de `dangerouslySetInnerHTML` (sauf portail, assaini côté serveur), CSP stricte |
| Vol de token | `access` en mémoire, `refresh` en cookie `HttpOnly` + `SameSite` + CSRF token |
| CSRF | Double submit cookie + vérification d'origine |
| Fuite tenant | `tenant_id` jamais envoyé par le client ; le serveur le déduit du token |
| Permissions | Masquage UI **et** contrôle serveur (l'UI n'est pas une sécurité) |
| Jetons dans les URLs | Interdit (pas de token en query string, y compris WebSocket) |
| Dépendances | `npm audit` + Dependabot en CI |

---

## 10. Tests

| Niveau | Outil | Couverture visée |
|---|---|---|
| Unitaires (format, calculs d'affichage, hooks) | Vitest | 60 % des modules `lib/` et `features/*/utils` |
| Composants (formulaires, tableaux) | Testing Library | Parcours de création de voucher, plan, routeur |
| End-to-end | Playwright | 8 scénarios : login, onboarding, vente, impression, désactivation, paiement, suspension, audit |
| Visuel | Playwright screenshots | 12 écrans, anti-régression |
| Accessibilité | axe-core en CI | 0 erreur critique sur les écrans principaux |

Les E2E tournent contre un backend de test avec un **routeur simulé** (backend factice) : la CI ne
dépend d'aucun matériel.

---

## 11. Design system minimal (à produire avant le code UI)

- Jetons : couleurs (primaire, sémantique succès/alerte/erreur), espacements, rayons, typographie.
- Composants : bouton, champ, sélecteur, tableau, modale, onglet, toast, bannière, carte de statut,
  badge, pagination, état vide, squelette.
- Statuts réseau codés **couleur + forme + texte** (accessibilité daltoniens).
- Deux thèmes : clair (défaut), sombre (techniciens).
- Gabarit du portail captif : variables de marque (`--brand`, logo, image de fond, message).
