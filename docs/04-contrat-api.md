# 04 — Contrat d'API (REST v1)

> Statut : **spécification** · Dernière mise à jour : 2026-11-01
> Base URL : `https://api.<domaine>/api/v1` · Format : JSON UTF-8 · Documentation générée : OpenAPI 3.1

---

## 1. Conventions

| Sujet | Décision |
|---|---|
| Versionnement | Préfixe d'URL `/api/v1` ; rupture = `/api/v2` (jamais de suppression silencieuse) |
| Nommage | Ressources au pluriel, `snake_case` dans le JSON, dates ISO 8601 UTC |
| Identifiants | UUID en chaîne |
| Pagination | Curseur (`?cursor=…&limit=50`), `limit` max 200 |
| Filtres | `?status=active&site_id=…&created_after=…` ; tri `?ordering=-created_at` |
| Champs | `?fields=id,name,status` pour alléger les réponses mobiles |
| Erreurs | RFC 9457 (`application/problem+json`) |
| Idempotence | En-tête `Idempotency-Key` obligatoire sur tous les `POST` financiers |
| Corrélation | `X-Request-ID` accepté et renvoyé ; propagé dans les logs et vers le routeur |
| Débit | 600 req/min/tenant, 60 req/min/utilisateur ; en-têtes `X-RateLimit-*` |
| Cache | `ETag` sur les listes stables (`plans`, `sites`) |
| Sécurité | HTTPS obligatoire, HSTS, CORS limité aux origines connues |

### Authentification

| Cas | Mécanisme |
|---|---|
| Console web | JWT : `access` (15 min) + `refresh` (7 j, rotation + détection de réutilisation) en cookie `HttpOnly`, `SameSite=Lax`, CSRF token |
| Portail captif | JWT court (30 min) lié au `device_id` + `mac` de l'utilisateur |
| Intégrations | `Authorization: Bearer sk_live_…` (token haché en base, scopes explicites) |
| Webhooks entrants (routeur/paiement) | HMAC-SHA256 du corps brut + horodatage ±300 s + liste d'IP |
| RADIUS | Secret partagé par routeur (jamais le même entre tenants) |

---

## 2. Format d'erreur

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Données invalides",
  "status": 422,
  "detail": "Le champ rate_down_kbps doit être supérieur à 0.",
  "instance": "/api/v1/plans",
  "request_id": "01J8Z3K9XQ",
  "errors": [{ "field": "rate_down_kbps", "code": "min_value", "message": "> 0" }]
}
```

Codes utilisés : `400` malformé, `401` non authentifié, `403` non autorisé (rôle insuffisant),
`404` introuvable dans **ce** tenant, `409` conflit (code voucher déjà utilisé), `422` validation,
`429` quota, `503` routeur injoignable (avec `retry_after`).

---

## 3. Arborescence des ressources

```
/auth            /tenants        /memberships     /sites
/devices         /devices/{id}/actions               /device-events
/plans           /voucher-batches /vouchers          /subscribers
/subscriptions   /invoices       /payments          /sessions
/usage           /alerts         /audit-logs        /webhooks
/portal          /me
```

---

## 4. Endpoints — authentification et compte

| Méthode | Chemin | Rôle requis | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Crée utilisateur + tenant (essai 14 j) |
| POST | `/auth/login` | — | Renvoie `access`, pose le cookie `refresh` |
| POST | `/auth/refresh` | — | Rotation du refresh token |
| POST | `/auth/logout` | membre | Révoque la session |
| POST | `/auth/password/reset` | — | Envoie un lien à usage unique |
| POST | `/auth/mfa/enable` \| `/auth/mfa/verify` | membre | TOTP |
| GET | `/me` | membre | Profil, tenants, rôles, permissions effectives |
| PATCH | `/me` | membre | Langue, téléphone, préférences |
| GET | `/me/sessions` | membre | Appareils connectés, révocation |

---

## 5. Endpoints — tenants et habilitations

| Méthode | Chemin | Rôle | Description |
|---|---|---|---|
| GET | `/tenants/current` | membre | Tenant actif (branding, quotas, usage) |
| PATCH | `/tenants/current` | admin | Nom, branding, fuseau, options |
| GET | `/tenants/current/usage` | admin | Routeurs/clients actifs vs quotas de l'offre |
| GET | `/memberships` | admin | Liste des membres |
| POST | `/memberships/invite` | admin | Invitation par e-mail, rôle cible |
| PATCH | `/memberships/{id}` | owner | Change le rôle |
| DELETE | `/memberships/{id}` | owner | Retire l'accès |
| GET/POST | `/api-tokens` | admin | Jetons d'intégration (le secret n'est affiché qu'une fois) |
| DELETE | `/api-tokens/{id}` | admin | Révocation |

---

## 6. Endpoints — parc réseau

| Méthode | Chemin | Description |
|---|---|---|
| GET/POST | `/sites` | Sites (nom, ville, adresse) |
| GET/PATCH/DELETE | `/sites/{id}` | |
| GET/POST | `/devices` | Inventaire des routeurs |
| GET/PATCH/DELETE | `/devices/{id}` | |
| POST | `/devices/{id}/enroll` | Génère le script d'enrôlement + secret (affiché une fois) |
| POST | `/devices/{id}/actions/test-connection` | Teste REST puis binaire |
| POST | `/devices/{id}/actions/sync` | Lance une réconciliation |
| POST | `/devices/{id}/actions/backup` | Sauvegarde la configuration |
| POST | `/devices/{id}/actions/reboot` | ⚠️ confirmation obligatoire, auditée |
| GET | `/devices/{id}/health` | CPU, RAM, uptime, version, température |
| GET | `/devices/{id}/interfaces` | Interfaces + débits calculés |
| GET | `/devices/{id}/events` | Journal d'événements du routeur |
| GET | `/devices/{id}/backups` | Historique + `GET …/backups/{bid}/download` |
| GET | `/device-events` | Flux global (filtrable par tenant/site/type) |

### Exemple : enrôlement

```http
POST /api/v1/devices/1f0c.../enroll
Content-Type: application/json

{ "transport": "wireguard", "use_rest": true }
```

```json
{
  "device_id": "1f0c...",
  "management_ip": "10.66.1.14",
  "script": "/interface wireguard add name=wg-saas ...",
  "expires_at": "2026-11-01T20:00:00Z",
  "instructions_url": "https://docs.../enrolement"
}
```

> Le script contient un secret à usage unique : il n'est **jamais** réaffichable (il faut le régénérer).

---

## 7. Endpoints — offres, vouchers, clients

| Méthode | Chemin | Description |
|---|---|---|
| GET/POST | `/plans` | Forfaits (prix, durée, quota, débit) |
| GET/PATCH/DELETE | `/plans/{id}` | |
| POST | `/plans/{id}/sync-router` | Pousse le profil hotspot/PPP correspondant |
| GET/POST | `/voucher-batches` | Génère un lot : `{plan_id, quantity, prefix}` |
| GET | `/voucher-batches/{id}` | Détail + statistiques d'utilisation |
| GET | `/voucher-batches/{id}/pdf` | PDF prêt à imprimer (1 à 500 coupons, QR inclus) |
| POST | `/voucher-batches/{id}/void` | Annule les vouchers non utilisés |
| GET | `/vouchers` | Filtres : `status`, `plan_id`, `batch_id`, `q` (code) |
| GET | `/vouchers/{id}` | Détail + sessions liées |
| POST | `/vouchers/{id}/revoke` | Révocation (déconnecte la session en cours) |
| POST | `/vouchers/{id}/extend` | Prolonge (durée/quota) |
| POST | `/vouchers/import` | CSV : `code,plan,quantity` |
| GET/POST | `/subscribers` | Clients récurrents (PPPoE) |
| GET/PATCH/DELETE | `/subscribers/{id}` | |
| POST | `/subscribers/{id}/actions/suspend` \| `resume` | |
| GET/POST | `/subscriptions` | Abonnements |
| POST | `/subscriptions/{id}/renew` | Prolonge et facture |
| GET | `/sessions` | Sessions (actives ou historiques) |
| DELETE | `/sessions/{id}` | Déconnexion forcée (CoA puis API) |
| GET | `/usage/summary` | Agrégats : `?group_by=device|plan|day` |

### Exemple : génération de lot

```http
POST /api/v1/voucher-batches
Idempotency-Key: 7d1f2c44-...

{ "plan_id": "0b9a...", "quantity": 100, "prefix": "KAD", "device_id": "1f0c..." }
```

```json
{
  "id": "9c2e...",
  "quantity": 100,
  "codes_preview": ["KAD-4821", "KAD-7734", "KAD-1190"],
  "pdf_url": "/api/v1/voucher-batches/9c2e.../pdf",
  "sync": { "queued": true, "task_id": "t_8891" }
}
```

Le provisioning sur le routeur est **asynchrone** : la réponse ne dépend pas du routeur.
`GET /voucher-batches/{id}` expose `sync_state` (`pending` → `synced` / `partial` / `failed`).

---

## 8. Endpoints — facturation et paiements

| Méthode | Chemin | Description |
|---|---|---|
| GET/POST | `/invoices` | Factures (brouillon ou émises) |
| GET | `/invoices/{id}` | Détail + lignes |
| POST | `/invoices/{id}/issue` \| `/void` | Émission, annulation |
| GET | `/invoices/{id}/pdf` | PDF |
| GET | `/payments` | Journal des paiements |
| POST | `/payments/manual` | Encaissement espèces / virement (rôle caissier) |
| POST | `/payments/initiate` | Paiement mobile money (renvoie `payment_id`, statut `pending`) |
| POST | `/payments/{id}/refund` | Remboursement (rôle admin) |
| GET | `/payments/{id}` | Statut, référence opérateur |
| GET | `/reports/revenue` | CA par jour/site/offre, encaissements par opérateur |

### Cycle d'un paiement mobile money

```
POST /payments/initiate → 202 { payment_id, status: "pending", ussd_hint: "Validez sur votre téléphone" }
        ↓ (webhook agrégateur, signé)
GET /payments/{id} → 200 { status: "succeeded", voucher: { code, plan } }
```

La console interroge `GET /payments/{id}` toutes les 3 s (ou reçoit l'événement via WebSocket).

---

## 9. Endpoints — supervision, audit, intégrations

| Méthode | Chemin | Description |
|---|---|---|
| GET | `/alerts` | Alertes (`status=firing`) |
| POST | `/alerts/{id}/ack` \| `/resolve` | Acquittement |
| GET/POST | `/alert-rules` | Règles (seuils, canaux) |
| GET | `/audit-logs` | Journal d'audit (filtres acteur/action/objet) |
| GET | `/dashboard` | Agrégat unique pour l'écran d'accueil (1 requête, < 300 ms) |
| GET/POST | `/webhooks` | Abonnements sortants (URL, événements, secret) |
| POST | `/webhooks/{id}/test` | Envoie un événement de test |

### Événements sortants (webhooks)

```
device.online / device.offline / device.config_changed
voucher.used / voucher.expired
session.started / session.stopped
payment.succeeded / payment.failed
invoice.issued / invoice.overdue
alert.firing / alert.resolved
```

En-têtes : `X-Event-Type`, `X-Delivery-ID`, `X-Signature: t=…,v1=HMAC_SHA256(t + "." + body)`.
Politique : 5 tentatives (1 s, 10 s, 1 min, 10 min, 1 h), désactivation après 48 h d'échec.

---

## 10. Endpoints internes (non publics)

| Méthode | Chemin | Appelant | Sécurité |
|---|---|---|---|
| POST | `/internal/radius/authorize` | FreeRADIUS | mTLS ou réseau privé |
| POST | `/internal/radius/accounting` | FreeRADIUS | idem |
| POST | `/hooks/device/{id}/heartbeat` | Routeur | `X-Device-Token` + IP WireGuard |
| POST | `/hooks/device/{id}/event` | Routeur (`/tool fetch`) | idem + HMAC |
| POST | `/hooks/payments/{provider}` | Agrégateur | HMAC + IP allowlist |
| POST | `/hooks/relay/{provider}` | Agrégateur (retry) | idem |

> Ces routes ne sont **pas** exposées dans l'OpenAPI public et sont filtrées par le reverse proxy
> (chemins `/internal` et `/hooks` sur des vhosts distincts).

---

## 11. WebSocket / temps réel

Endpoint : `wss://api.<domaine>/ws/v1/tenant` (JWT en sous-protocole, pas en query string).

| Canal | Charge utile | Fréquence |
|---|---|---|
| `devices.status` | `{device_id, status, last_seen_at}` | à chaque changement |
| `sessions.active` | `{device_id, count, bytes_total}` | 10 s (agrégé, pour éviter le bruit) |
| `payment.status` | `{payment_id, status}` | à chaque changement |
| `alerts` | `{alert}` | à chaque changement |

Repli automatique en HTTP polling (15 s) — indispensable en connexion instable.

---

## 12. Règles de conception à respecter

1. **Aucune route ne parle directement au routeur.** Toute action matérielle crée une tâche et
   renvoie `202 Accepted` avec `task_id`.
2. **Toute mutation est auditée** avec acteur, avant/après, IP.
3. **Toute somme d'argent** est calculée côté serveur, jamais acceptée du client.
4. **Toute écriture financière** exige `Idempotency-Key` (sinon `400`).
5. **Le tenant n'est jamais dans l'URL** : il vient du token. Une requête ne peut pas « changer de
   tenant » en modifiant un paramètre.
6. **404 plutôt que 403** sur une ressource d'un autre tenant (pas de fuite d'existence).
7. Les réponses de liste sont **toujours paginées**, même si elles contiennent 3 éléments.
8. Les champs calculés (`amount_due`, `is_online`) sont en lecture seule côté API.
9. Pas de PATCH partiel implicite : `PATCH` = fusion, `PUT` = remplacement complet.
10. Toute ressource expose `created_at`, `updated_at`, et `id` en premier champ.

---

## 13. Livrables OpenAPI

- `openapi/v1.yaml` généré depuis le code (drf-spectacular) puis **relu** (pas de `x-` magique).
- Collection Bruno/Insomnia versionnée pour les tests manuels.
- Tests de contrat en CI : le schéma doit valider toutes les réponses des tests fonctionnels.
- Page de documentation publique (`/docs`) générée depuis le schéma, avec exemples réels anonymisés.
