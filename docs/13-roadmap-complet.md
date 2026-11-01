# 13 — Roadmap complet du projet (A → Z)

> Statut : **plan directeur exécutable** · Dernière mise à jour : 2026-11-01
> Objectif de ce document : savoir **exactement** quoi faire, dans quel ordre, jusqu'à ce que le
> projet **fonctionne réellement** en production — puis ce qu'il reste à faire ensuite.
>
> Vocabulaire : `P` = phase, `T` = tâche numérotée, `✅` = fait, `⬜` = à faire.
> **Avancement au 2026-11-01** : P2 socle **livré**, P3 connecteur **en cours**.
> Fonctionne de bout en bout : espace → site → routeur → enrôlement (script + secrets chiffrés)
> → sonde → statut « en ligne » ; **authentification JWT** ; **console React** branchée sur
> l'API ; **connexion à un routeur RouterOS réel** (API REST, HTTP/HTTPS, port libre).
> **Ajout 2026-11-01** : P4 entamé — forfaits, lots de vouchers, envoi au routeur (REST),
> synchronisation des quotas, export CSV et écran console livrés et testés.
> Prochaine marche : PDF/QR des coupons (T42) puis RADIUS (P5).
> Chaque phase se termine par une **porte de sortie** (critères mesurables). On ne passe pas à la
> suivante sans l'avoir franchie.

---

## 0. Comment lire ce roadmap

1. **Les phases sont séquentielles** ; les tâches à l'intérieur d'une phase peuvent se paralléliser
   (front/back), sauf mention contraire.
2. **Chaque tâche est "terminée"** seulement si elle respecte la *Définition de Fini* (§11).
3. **Les portes de sortie sont des décisions**, pas des formalités : si une porte n'est pas franchie,
   options = corriger, réduire le périmètre, ou arrêter (critères d'arrêt §12).
4. Les durées sont données pour **2 développeurs à temps plein** (1 back, 1 front), hors imprévus.
5. Le suivi se fait dans ce fichier : on coche, on date, on note l'écart.

**Vue d'ensemble** (≈ 26 semaines jusqu'à la production, dont 20 de construction) :

| Phase | Nom | Durée | Sortie |
|---|---|---|---|
| P0 | Cadrage, validation, cadre juridique | 3 sem | Décision GO + 3 pilotes |
| P1 | Laboratoire technique | 2 sem | Hypothèses RouterOS/RADIUS validées |
| P2 | Socle applicatif (multi-tenant, auth, CI/CD) | 4 sem | Connexion + isolation multi-tenant prouvée |
| P3 | Parc réseau + connecteur MikroTik | 4 sem | Un vrai routeur enrôlé et piloté |
| P4 | Catalogue, vouchers, provisioning | 3 sem | 500 vouchers créés sur un routeur réel |
| P5 | AAA : RADIUS, sessions, quotas | 4 sem | Un client se connecte et se fait couper au quota |
| P6 | Caisse, portail captif, paiements | 4 sem | Un inconnu achète et se connecte seul |
| P7 | Supervision, alertes, exploitation | 2 sem | Une panne est détectée avant le client |
| P8 | Bêta pilotée | 4 sem | 10 routeurs, 3 clients payants |
| P9 | Mise en production + run | 1 sem | SLA affiché, astreinte en place |
| P10 | V2 : FAI/PPPoE, industrialisation | continu | Facturation récurrente, 2e vertical |

---

## P0 — Cadrage, validation et cadre juridique (3 semaines)

**But** : ne pas construire un produit que personne ne paie.

| # | Tâche | Livrable | État |
|---|---|---|---|
| T01 | 10 entretiens (cybercafés, hôtels, petits FAI, installateurs) | Notes écrites + 3 douleurs chiffrées | ⬜ |
| T02 | Test de prix oral (question directe, 3 paliers) | Fourchette acceptée | ⬜ |
| T03 | Récupérer 3 accès routeurs pilotes + 1 routeur de test | 3 accords écrits | ⬜ |
| T04 | Décisions D1–D10 tranchées (`10-checklists.md` §2) | Décisions consignées | ✅ partiel |
| T05 | Cadre juridique : CGU, confidentialité, sous-traitance, ARPCE/CIL | Documents relus par un juriste | ⬜ |
| T06 | Ouverture du compte agrégateur mobile money | Compte en test | ⬜ (délai 4–8 sem.) |
| T07 | Dépôt, CI minimale, conventions de code | `docs/14-conventions-de-code.md` appliqué | ✅ |

**Porte de sortie P0** : 3 pilotes engagés **et** le prix tenu en entretien.
Sinon → revoir le vertical (voir `00-vision-et-produit.md`).

---

## P1 — Laboratoire technique (2 semaines)

**But** : lever les incertitudes techniques avant d'écrire du produit. Aucune de ces tâches ne doit
être sous-traitée « plus tard » : elles conditionnent tout le reste.

| # | Tâche | Détail | État |
|---|---|---|---|
| T10 | 3 CHR opérationnels | RouterOS 7.11, 7.16, 7.18 (QEMU/Proxmox), snapshots | ⬜ |
| T11 | Client REST | `GET /rest/system/resource`, `PUT /rest/ip/hotspot/user`, erreurs | ⬜ |
| T12 | Client API binaire | login 8729, `print` avec `.proplist`, `!trap`, timeout | ⬜ |
| T13 | `listen` | abonnement + `cancel` + reconnexion après coupure réseau | ⬜ |
| T14 | WireGuard derrière NAT | routeur → hub, latence, reconnexion, MTU | ⬜ |
| T15 | FreeRADIUS + hotspot | `Access-Accept`, `Interim-Update`, `Session-Timeout` | ⬜ |
| T16 | **Test critique** : RADIUS arrêté | Le hotspot bascule-t-il sur les utilisateurs locaux ? | ⬜ |
| T17 | Routeur physique bas de gamme | CPU/mémoire avec 500 utilisateurs + 30 sessions | ⬜ |
| T18 | Journal de validation | `docs/11-journal-de-validation.md` rempli | ⬜ |

**Porte de sortie P1** : T16 et T14 validés. Sinon, l'architecture change **maintenant**, pas en P5.

---

## P2 — Socle applicatif (4 semaines)

**But** : une application vide mais **solide** : on se connecte, on a un tenant, l'isolation est prouvée.

| # | Tâche | Détail | État |
|---|---|---|---|
| T20 | Projet Django + DRF + settings par environnement minimal | `backend/config/` | ✅ |
| T21 | `core` : modèles abstraits, `TenantContext`, exceptions, `BaseService` | Héritage prêt à l'emploi | ✅ |
| T22 | `tenants` : Tenant, création, essai 14 jours | Service + tests | ✅ |
| T23 | `accounts` : User custom, Membership, rôles | Service + tests | ✅ (modèles, rôles, sélecteurs) |
| T24 | Auth JWT (access 15 min, refresh 7 j, rotation) | Endpoints + tests | ✅ |
| T25 | Permissions par rôle + middleware tenant | Test d'isolation sur chaque endpoint | ✅ (middleware + mixin JWT + 8 tests d'isolation) |
| T26 | Console React : layout, login, garde de route | `frontend/apps/console` | ✅ (`frontend/console`, 4 écrans) |
| T27 | CI/CD (lint, tests, migrations, build) | `.github/workflows` | ⬜ |
| T28 | Staging + sauvegardes + supervision | `infra/` | ⬜ |

**Porte de sortie P2** : un test automatisé prouve qu'un tenant ne peut **jamais** lire les données
d'un autre (liste + détail + action). CI verte et bloquante.

---

## P3 — Parc réseau et connecteur MikroTik (4 semaines)

**But** : le cœur différenciant. Un vrai routeur est ajouté, enrôlé, interrogé et suivi.

| # | Tâche | Détail | État |
|---|---|---|---|
| T30 | `network` : Site, Device, DeviceCredential chiffré, statut | Modèles + index | ✅ |
| T31 | `mikrotik.schemas` : objets normalisés (`SystemInfo`, `DeviceHealth`) | Indépendants du backend | ✅ |
| T32 | `BaseBackend` + `FakeBackend` | Tests sans matériel | ✅ |
| T33 | `RestBackend` (httpx) | Timeouts, `!trap`, TLS | ◐ (lecture complète, HTTP/HTTPS, port libre ; écritures en P4) |
| T34 | `BinaryBackend` (librouteros) | 8729, `.proplist`, reconnexion | ⬜ |
| T35 | `MikroTikService` : test de connexion, santé, synchronisation | 1 responsabilité par méthode | ✅ (sonde + santé) |
| T36 | Enrôlement : génération du script + secret à usage unique + WireGuard | Idempotent, 15 min max | ⬜ |
| T37 | Heartbeat routeur (`/tool fetch`) + endpoint signé | Détection online/offline | ⬜ |
| T38 | `ProvisioningTask` + worker Celery + réconciliation | Rejouable, états | ◐ (worker de sonde ; provisioning en P4) |
| T39 | Fiche routeur (React) branchée sur l'API réelle | Onglets vue d'ensemble | ✅ |

**Porte de sortie P3** : un routeur physique est enrôlé **en moins de 15 minutes**, apparaît en ligne
dans la console, remonte version/CPU, et le rejoue sans créer de doublon.

---

## P4 — Catalogue, vouchers et provisioning (3 semaines)

| # | Tâche | Détail | État |
|---|---|---|---|
| T40 | `catalog` : Plan (prix, durée, quota, débit) | Validation métier stricte | ✅ |
| T41 | `vouchers` : Lot, code anti-ambigu (sans I/O/0/1), statuts | Unicité par tenant | ✅ |
| T42 | Génération PDF + QR (WeasyPrint), 1 à 500 coupons | < 30 s | ⬜ |
| T43 | Import/export CSV | Idempotent, rapport d'erreurs | ◐ (export CSV livré, import à venir) |
| T44 | Provisioning des profils et des utilisateurs hotspot | `upsert` + marquage `kora:` | ✅ |
| T45 | Écran vouchers + aperçu du coupon | React | ◐ (écran livré, aperçu imprimable à venir) |
| T46 | Réconciliation quotidienne (base ↔ routeur) | Rapport d'écarts | ◐ (écarts détectés par `sync`, correction auto à faire) |

**Porte de sortie P4** : 500 vouchers générés puis visibles sur un hAP ac², imprimables, et un écart
volontaire (suppression manuelle sur le routeur) est détecté puis corrigé automatiquement.

---

## P5 — AAA : RADIUS, sessions, quotas (4 semaines)

**But** : le temps réel. C'est ici que le produit devient un vrai outil d'exploitation.

| # | Tâche | Détail | État |
|---|---|---|---|
| T50 | FreeRADIUS + schéma (radcheck, radreply, radacct) avec `tenant_id` | Résolution du tenant par NAS | ⬜ |
| T51 | Endpoints internes `/internal/radius/{authorize,accounting}` | mTLS ou réseau privé | ⬜ |
| T52 | Attribution des attributs (rate-limit, quota, session-timeout) | Table de correspondance plans | ⬜ |
| T53 | Consolidation des sessions (`radacct` → `sessions`) | Idempotent, reprise | ⬜ |
| T54 | Quotas et coupure (CoA + repli API) | Effet < 5 s | ⬜ |
| T55 | Écran sessions actives (WebSocket + repli polling) | React | ⬜ |
| T56 | Test de résilience : RADIUS arrêté 10 min | Clients non coupés, reprise propre | ⬜ |

**Porte de sortie P5** : un client se connecte avec un voucher, consomme, atteint son quota, est
déconnecté automatiquement, et la console l'affiche en moins de 15 s.

---

## P6 — Caisse, portail captif et paiements (4 semaines)

| # | Tâche | Détail | État |
|---|---|---|---|
| T60 | Caisse : vente, journal, reçu PDF, clôture | 3 clics, testé au clavier | ⬜ |
| T61 | Portail captif par tenant (logo, couleurs, textes) | < 1 s en 3G | ⬜ |
| T62 | Abstraction agrégateur + `POST /payments/initiate` | Un adaptateur par opérateur | ⬜ |
| T63 | Webhook signé, idempotent, réconciliation | Double événement = 1 voucher | ⬜ |
| T64 | Achat de bout en bout (forfait → paiement → code → connexion) | 1 utilisateur externe réussit seul | ⬜ |
| T65 | Reçus, notifications WhatsApp/e-mail | Gabarits FR | ⬜ |
| T66 | Rapports : CA par jour/site/offre, export CSV | Exactitude vérifiée à la main | ⬜ |

**Porte de sortie P6** : 10 achats réels (petits montants) passent sans intervention manuelle, et la
réconciliation ne montre aucun écart.

---

## P7 — Supervision, alertes et exploitation (2 semaines)

| # | Tâche | Détail | État |
|---|---|---|---|
| T70 | Règles d'alerte (routeur down, disque, CPU, quota, certificat) | Anti-bruit (durée, seuil) | ⬜ |
| T71 | Notifications et page de statut publique | `status.<domaine>` | ⬜ |
| T72 | Journal d'audit immuable + export | 24 mois | ⬜ |
| T73 | Métriques et tableaux de bord internes (Sentry, Prometheus) | Alertes d'exploitation | ⬜ |
| T74 | 8 runbooks d'incident | Rédigés et testés à blanc | ⬜ |
| T75 | Sauvegarde restaurée sur un environnement neuf | Procès-verbal daté | ⬜ |

**Porte de sortie P7** : on débranche un routeur → alerte en < 2 min ; on restaure la base sur une
machine neuve en < 2 h, chronométré.

---

## P8 — Bêta pilotée (4 semaines)

| # | Tâche | Détail | État |
|---|---|---|---|
| T80 | 10 routeurs chez 5 clients, accompagnement sur site | 14 jours sans incident bloquant | ⬜ |
| T81 | Formation de 30 min par client (caissier + technicien) | Fiche mémo 1 page | ⬜ |
| T82 | Support : canal, horaires, base de connaissances (10 articles) | Réponse < 4 h ouvrées | ⬜ |
| T83 | Corrections issues du terrain (P1 uniquement) | Zéro bug critique ouvert | ⬜ |
| T84 | Tarification testée, 3 contrats signés | Encaissement effectif | ⬜ |
| T85 | Tableau de bord interne (usage, MRR, incidents) | Revue hebdomadaire | ⬜ |

**Porte de sortie P8** : 3 clients **paient**, l'usage est hebdomadaire, le support reste < 2 h par
client et par semaine. Sinon → pivoter ou resserrer l'offre.

---

## P9 — Mise en production et exploitation courante (1 semaine + continu)

| # | Tâche | Détail | État |
|---|---|---|---|
| T90 | Checklist go-live (`10-checklists.md` §5) entièrement cochée | Signée | ⬜ |
| T91 | SLA affiché, astreinte, procédure d'escalade | Documenté | ⬜ |
| T92 | Contrats, facturation de nos clients, relances | Automatisé | ⬜ |
| T93 | Revue de sécurité (dépendances, secrets, accès) | Rapport trimestriel | ⬜ |
| T94 | Plan de reprise testé (RTO/RPO) | Trimestriel | ⬜ |

**Porte de sortie P9** : le produit tourne **sans intervention des développeurs pendant 2 semaines**.
C'est la définition de « le projet marche ».

---

## P10 — V2 et industrialisation (continu)

| # | Chantier | Pourquoi | Quand |
|---|---|---|---|
| T100 | Abonnés PPPoE + facturation récurrente + relances | Ticket moyen ×5 | Dès 3 demandes |
| T101 | Marque blanche complète (domaine client, e-mails) | Argument de vente | 6 premiers clients |
| T102 | API publique + webhooks documentés | Intégrateurs, revendeurs | 10 clients |
| T103 | Application mobile technicien (React Native) | Terrain | > 5 techniciens actifs |
| T104 | Sauvegarde/diff/restauration de configuration | Rétention | Avant 100 routeurs |
| T105 | Sharding du connecteur, réplique RADIUS | Charge | > 200 routeurs |
| T106 | Multi-langue (EN) | Expansion régionale | Après validation BF |

---

## 11. Définition de Fini (s'applique à **chaque** tâche)

Une tâche n'est terminée que si **les 8 points** sont vrais :

1. **Code en couches** : la vue ne contient aucune logique métier (voir `14-conventions-de-code.md`).
2. **Tests** : au moins un test heureux + un test d'erreur ; couverture ≥ 90 % sur `mikrotik`,
   `billing`, `aaa`, ≥ 70 % ailleurs.
3. **Isolation** : test prouvant qu'un autre tenant n'y accède pas (si la tâche touche des données).
4. **Idempotence** : rejouer l'action ne crée ni doublon ni incohérence.
5. **Traçabilité** : entrée d'audit pour toute action sensible ; logs sans secret.
6. **Erreur utile** : message en français, avec cause probable et action.
7. **Observabilité** : au moins une métrique ou un log structuré exploitable en production.
8. **Documentation** : docstrings complètes, et mise à jour du document concerné dans `docs/`.

---

## 12. Carte des jalons et critères d'arrêt

| Jalon | Date cible | Décision |
|---|---|---|
| J1 — Fin P0 | S+3 | GO / pivot de vertical si < 3 pilotes |
| J2 — Fin P1 | S+5 | GO technique si RADIUS-off et WireGuard validés |
| J3 — Fin P3 | S+13 | Démo d'un routeur réel piloté → GO commercial prudent |
| J4 — Fin P5 | S+20 | Le produit « fait le travail » d'un cybercafé |
| J5 — Fin P8 | S+26 | GO production si 3 clients paient et support maîtrisé |

**Critères d'arrêt (à assumer à l'avance)** :
- Aucun pilote après 6 semaines de démarchage → le besoin n'est pas là où on le croit.
- Coût de support > 30 % du MRR après 10 clients → l'offre est mal calibrée (trop de personnalisation).
- Impossible de fiabiliser la connexion aux routeurs après P3 → changer d'approche (agent local,
  partenariat avec un hébergeur local, ou pivot vers le fleet management pur).

---

## 13. Ordre de travail réel (sprints de 1 semaine)

| Sprint | Backend | Frontend | Sortie démontrable |
|---|---|---|---|
| S1 | Socle `core` + `tenants` + tests isolation | Setup Vite + layout + login factice | « je me connecte, je vois mon espace » |
| S2 | `network` + `MikroTikGateway` + FakeBackend | Liste des routeurs | « mes routeurs sont listés » |
| S3 | `RestBackend` + test de connexion | Fiche routeur | « je clique, ça interroge un vrai CHR » |
| S4 | Enrôlement + script + heartbeat | Assistant d'enrôlement | « j'ajoute un routeur en 15 min » |
| S5 | `catalog` + `vouchers` (génération) | Forfaits + générateur | « je génère 100 codes » |
| S6 | Provenance routeur + PDF/QR | Aperçu et impression | « mes coupons sortent » |
| S7–S8 | RADIUS + sessions + quotas | Sessions temps réel | « un client consomme et se fait couper » |
| S9 | Paiement + webhooks | Portail captif | « un inconnu achète et se connecte » |
| S10 | Alertes + audit + rapports | Alertes + caisse | « je vois mes recettes et mes pannes » |

**Sprint 1 = ce qui est codé maintenant** : `core`, `tenants`, `network` (modèles), `mikrotik`
(interface + FakeBackend + service), une vue API fine, et les tests qui prouvent l'isolation.

---

## 14. Ce qui fait qu'on peut dire « le projet marche »

Le projet est considéré comme **opérationnel** quand ces 8 affirmations sont vraies et vérifiables :

1. Un cybercafé crée son compte seul et enrôle son routeur en **< 15 min** sans aide.
2. Il génère, imprime et vend des vouchers ; un client se connecte avec le code en **< 1 min**.
3. La consommation remonte en base en **< 5 min** (Interim-Update) et le quota coupe la session.
4. Un client peut acheter en ligne par mobile money et se connecter **sans intervention humaine**.
5. Une panne de routeur est signalée **avant** l'appel du client.
6. Une panne de notre plateforme **ne coupe pas** les clients déjà connectés.
7. Chaque euro encaissé est traçable (audit + journal de caisse + réconciliation).
8. Une restauration complète est possible en **< 2 h** avec un procès-verbal daté.

Tant qu'un de ces points est faux, le projet n'est pas « fini » — il est en construction.
