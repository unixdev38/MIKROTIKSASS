# 16 · Vouchers hotspot : génération, envoi au routeur, quotas

> **But** : vendre des codes d'accès prépayés sur un cybercafé/hôtel, les pousser sur le
> routeur MikroTik, puis suivre leur consommation — y compris avec le routeur x86 de ta VM.
>
> Ce document décrit ce qui est **livré et testé**, pas une intention.

---

## 1. Les trois objets

| Objet | Rôle | Table |
|---|---|---|
| **Plan** (forfait) | ce que tu vends : 1 h / 200 FCFA, 50 Mo, débit 2M/2M | `hotspot_plan` |
| **VoucherBatch** (lot) | une génération de N codes pour un site + un forfait | `hotspot_voucherbatch` |
| **Voucher** (code) | un coupon vendable = un utilisateur hotspot | `hotspot_voucher` |

Cycle de vie d'un code :

```
unused ──envoi──► provisioned ──1re connexion──► active ──► exhausted (quota)
   │                   │                            └─────► expired  (durée)
   └───────────────────┴──────── révocation ──────────────► revoked
```

Les codes évitent les caractères confondables (`0/O`, `1/I/L`, `5/S`, `2/Z`) : un code se
lit au téléphone sans erreur. Format : `PRÉFIXE-XXXXXXXX` (8 caractères utiles).

---

## 2. Ce que le routeur reçoit

Pour chaque code, l'API REST crée un **utilisateur hotspot** :

```http
PUT /rest/ip/hotspot/user
{"name":"CC01-K7QF9M3X","password":"CC01-K7QF9M3X",
 "limit-uptime":"1h","limit-bytes-total":"52428800",
 "rate-limit":"2M/2M","comment":"kora:<uuid-du-lot>"}
```

- `limit-uptime` ← `Plan.duration_minutes` (`60` → `1h`, `90` → `1h30m`, `1440` → `1d`).
- `limit-bytes-total` ← `Plan.data_cap_mb` (`0` = champ absent = illimité).
- `rate-limit` ← `Plan.rate_limit` (vide = pas de bridage).
- Le commentaire `kora:<lot>` permet de retrouver l'origine d'un utilisateur sur le routeur.

L'opération est **idempotente** : si l'utilisateur existe déjà, un `PATCH` met à jour ses
limites au lieu d'un doublon. Rejouer un lot est donc sans risque.

Équivalent en CLI RouterOS (ce que produit notre appel) :

```
/ip hotspot user add name=CC01-K7QF9M3X password=CC01-K7QF9M3X \
    limit-uptime=1h limit-bytes-total=52428800 rate-limit=2M/2M comment="kora:…"
```

Suppression (révocation) : `DELETE /rest/ip/hotspot/active/<id>` puis
`DELETE /rest/ip/hotspot/user/<id>` — la session ouverte est coupée, pas seulement le compte.

---

## 3. Quotas : qui coupe quoi

| Mécanisme | Qui l'applique | Effet |
|---|---|---|
| `limit-uptime` | le routeur | déconnexion à la fin de la durée |
| `limit-bytes-total` | le routeur | déconnexion dès le volume atteint |
| `rate-limit` | le routeur | bridage du débit |
| `sync` (plateforme) | nos workers | **reflète** l'état : consommé, activé, épuisé, expiré |

Point important et volontairement honnête : **la coupure est faite par RouterOS**, pas par
notre base. Notre synchronisation lit `bytes-in` / `bytes-out` / `uptime` et marque le code
`exhausted` ou `expired`. C'est ce qui rend le produit utilisable même si le SaaS est
momentanément injoignable — et c'est aussi la limite du mode « vouchers » : sans RADIUS,
on ne peut pas couper un client à la seconde près depuis le serveur (prévu en P5).

---

## 4. API

| Méthode | Endpoint | Rôle |
|---|---|---|
| `GET/POST` | `/api/v1/plans/` | catalogue (`?include_inactive=1` pour tout voir) |
| `GET/POST` | `/api/v1/voucher-batches/` | lots + compteurs par état |
| `POST` | `/api/v1/voucher-batches/{id}/provision/` | envoi au routeur |
| `POST` | `/api/v1/voucher-batches/{id}/sync/` | relecture des compteurs |
| `GET` | `/api/v1/voucher-batches/{id}/export/` | CSV (caisse / impression) |
| `GET` | `/api/v1/vouchers/?batch=…&state=…` | codes, filtrables |
| `POST` | `/api/v1/vouchers/{id}/revoke/` | révocation + retrait du routeur |

Rôles : `viewer` lit, `technician` génère et pousse, `admin` crée les forfaits.
Les erreurs suivent `application/problem+json` avec un code stable
(`plan_code_taken`, `batch_quantity_invalid`, `site_without_device`…).

Exemple complet en trois appels :

```bash
TOKEN=$(curl -s -X POST localhost:8001/api/v1/auth/token/ -H 'Content-Type: application/json' \
  -d '{"email":"demo@kora.bf","password":"demo-mot-de-passe-2026"}' | jq -r .access)

curl -s -X POST localhost:8001/api/v1/voucher-batches/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"site_id":"…","plan_id":"…","quantity":20,"prefix":"CC01"}'

curl -s -X POST localhost:8001/api/v1/voucher-batches/<id>/provision/ -H "Authorization: Bearer $TOKEN"
curl -s localhost:8001/api/v1/voucher-batches/<id>/export/ -H "Authorization: Bearer $TOKEN" -o codes.csv
```

---

## 5. Dans la console

**Vouchers** (barre latérale) :

1. **Nouveau forfait** → nom, code, durée, volume, prix, débit.
2. **Générer un lot** → site, forfait, quantité, préfixe ; la valeur du lot s'affiche en direct.
3. **Envoyer** → pousse les codes sur le routeur du site (ou celui forcé sur le lot).
4. **Sync** → remonte consommé / activés / épuisés.
5. **CSV** → fichier prêt à imprimer (`code,password,forfait,duree,volume_mo,prix_fcfa,site,etat`).

La table des codes se filtre par état (générés, sur le routeur, utilisés, quota épuisé, révoqués).

---

## 6. Tester sur ton routeur VirtualBox

Prérequis : un serveur hotspot actif sur le routeur (sinon RouterOS refuse l'écriture).

```
/interface bridge add name=bridge-hotspot
/ip address add address=10.5.50.1/24 interface=bridge-hotspot
/ip pool add name=hs-pool ranges=10.5.50.10-10.5.50.200
/ip hotspot profile add name=kora-hs hotspot-address=10.5.50.1 dns-name=hotspot.kora login-by=http-chap,cookie
/ip hotspot add name=hs-kora interface=bridge-hotspot address-pool=hs-pool profile=kora-hs
```

Puis, dans la console : **Routeurs → ta VM → Connecter le routeur** (identifiants `kora`,
HTTPS, port 443), **Tester la connexion**, puis **Vouchers → Générer → Envoyer**.

Vérification côté routeur :

```
/ip hotspot user print where comment~"kora"     ; nos codes
/ip hotspot active print                        ; sessions ouvertes
```

| Symptôme | Cause | Solution |
|---|---|---|
| `HTTP 400 : … does not match any value of profile` | aucun serveur hotspot | créer le hotspot (§6) |
| `HTTP 403` | policy `rest-api` manquante | `/user group set kora policy=read,write,api,rest-api,test` |
| `0 code(s) envoyé(s)` | codes déjà `revoked`/`exhausted` | générer un nouveau lot |
| `site_without_device` | aucun routeur sur le site | ajouter le routeur au site |

---

## 7. Ce qui reste à faire (assumé)

| Sujet | État |
|---|---|
| Génération PDF + QR des coupons | ⬜ P4 (T42) |
| Réconciliation automatique du parc (écart base ↔ routeur) | ◐ la synchro détecte (`unknown`), la correction auto reste à faire |
| Profils hotspot personnalisés par forfait | ⬜ (les limites sont posées par utilisateur, ce qui suffit) |
| Coupure à la seconde / session live | ⬜ P5 — RADIUS |
| Vente et encaissement des codes (caisse) | ⬜ P6 |
