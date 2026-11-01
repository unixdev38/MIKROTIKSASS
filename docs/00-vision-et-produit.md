# 00 — Vision, produit et marché

> Statut : **brouillon de conception à valider** · Dernière mise à jour : 2026-11-01
> Ce document répond à : *que peut-on créer avec l'API MikroTik, pour qui, et pourquoi ?*

---

## 1. Ce que l'API MikroTik permet réellement

RouterOS expose **tout** son arbre de configuration via deux interfaces programmables :

| Interface | Transport | Ce qu'elle permet | Usage typique dans un SaaS |
|---|---|---|---|
| **API binaire** | TCP 8728 (clair) / 8729 (TLS) | Lecture/écriture complète, requêtes filtrées, **écoute temps réel** (`listen`), exécution de commandes | Provisioning, supervision, sessions actives |
| **REST API** (RouterOS v7+) | HTTPS 443 (`/rest`) | CRUD JSON sur les mêmes menus, pas de streaming | Provisioning simple, intégrations, routeurs derrière un proxy |
| **RADIUS client** | UDP 1812/1813 (+ CoA 3799) | Authentification + comptabilité des clients (hotspot, PPPoE, DHCP, 802.1X) | **Cœur du billing temps réel** |
| **Scripts RouterOS** | `/tool fetch`, `/system scheduler` | Le routeur **pousse** des événements vers notre cloud | Contournement du NAT/CGNAT, alertes |
| **WireGuard / IPsec** | UDP 51820 / 500 | Tunnel permanent routeur → cloud | Accès sécurisé aux routeurs sans IP publique |

**Conséquence importante** : on ne « pilote » pas un routeur MikroTik comme une base de données. C'est un
équipement réseau, lent, sans transactions, avec des ressources CPU limitées. L'architecture doit donc
séparer strictement :

- le **plan de contrôle** (notre SaaS : config, abonnés, facturation) ;
- le **plan de données / AAA** (RADIUS : authentification et comptabilité temps réel) ;
- le **plan utilisateur** (le trafic Internet des clients finaux ne traverse **jamais** notre plateforme).

---

## 2. Quatre produits possibles — analyse comparative

### Produit A — « Hotspot & vouchers as a Service » (Wi-Fi payant)
Cible : cybercafés, hôtels, résidences, écoles, universités, opérateurs de hotspots de quartier, événements.
Fonctions : création de forfaits (durée / volume / débit), génération de tickets et QR codes,
portail captif personnalisé, achat en ligne par mobile money, coupure automatique en fin de forfait,
suivi des sessions, reversements.

- Valeur : remplace les carnets de tickets manuscrits et les feuilles Excel.
- Complexité : **moyenne**. Le plus rapide à monétiser.
- Concurrence : User Manager intégré (gratuit mais local au routeur), mkcontroller, TangoWave, scripts maison.

### Produit B — « ISP-in-a-box » : gestion d'abonnés PPPoE / FTTH
Cible : petits FAI locaux, revendeurs Wi-Fi, opérateurs de quartier (10 → 2 000 abonnés).
Fonctions : dossiers abonnés, offres, prorata, factures, paiements mobile money, activation/suspension
automatique, gestion des adresses IP et des files d'attente (queues), support et tickets.

- Valeur : le recouvrement et la relance sont le vrai problème du FAI ; l'automatisation fait gagner de l'argent.
- Complexité : **élevée** (facturation, fiscalité, paiements, AAA, support).
- Concurrence : SPlynx, Sonar, Radius Manager (DMA), OpenWISP, solutions locales.

### Produit C — « Fleet manager » : supervision et configuration de parc
Cible : intégrateurs, revendeurs MikroTik, PME multi-sites, ONG.
Fonctions : inventaire des routeurs, sauvegarde automatique des configs et diff, mises à jour de
firmware planifiées, alertes (CPU, température, liens, IP publique changée), déploiement de
configurations types, VPN de management.

- Valeur : un technicien gère 5× plus de sites sans se déplacer.
- Complexité : **moyenne**. Excellent produit d'appel (freemium).
- Concurrence : The Dude, Zabbix + scripts, mkcontroller, solutions NMS génériques.

### Produit D — Plateforme unifiée (A + B + C)
Une seule base de tenants, une seule console, facturation par site/abonné. C'est la cible naturelle,
mais il ne faut **pas** la construire d'un coup : le MVP doit n'être qu'un des trois premiers.

### Tableau de décision

| Critère | A — Hotspot | B — FAI/PPPoE | C — Fleet | D — Unifié |
|---|---|---|---|---|
| Time-to-market | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★☆☆☆☆ |
| Ticket moyen | ★★☆☆☆ | ★★★★★ | ★★★☆☆ | ★★★★★ |
| Complexité technique | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★★★ |
| Dépendance API MikroTik | moyenne (RADIUS) | forte | forte | forte |
| Risque de concurrence | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ |
| Effet de rétention | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★★★ |

### **Recommandation**

> **Démarrer par A (hotspot/vouchers) avec, dès la conception, le socle multi-tenant et le module
> dispositifs de C. Puis attaquer B en V2**, en réutilisant RADIUS, la facturation et le provisioning.

Raison : A apporte des utilisateurs en quelques semaines et force à maîtriser le trio
`provisioning ↔ RADIUS ↔ paiement`. B se vend beaucoup plus cher mais exige une facturation
complète et un support lourd : le construire après avoir validé la demande évite de brûler la trésorerie.

---

## 3. Personas

| Persona | Contexte | Douleur n°1 | Ce qu'il paiera |
|---|---|---|---|
| **Ali, 34 ans** — gère 3 cybercafés à Ouagadougou | 12 routeurs hAP, tickets papier, 2 employés | Il ne sait pas qui a payé ; les clients repartent avec 2 h de crédit non consommées | 10 000–20 000 FCFA/mois pour ne plus compter les tickets |
| **Fatou, 41 ans** — petite FAI de quartier | 420 abonnés PPPoE, 1 technicien | 30 % d'impayés, coupures manuelles, relances par WhatsApp | 50 000–150 000 FCFA/mois si ça réduit les impayés |
| **M. Kaboré** — gérant d'hôtel 40 chambres | 4 bornes Wi-Fi, réception | Codes Wi-Fi partagés, aucun contrôle, plaintes clients | 15 000 FCFA/mois, portail à sa marque |
| **Issa, 26 ans** — installateur indépendant | 25 clients PME, WinBox à distance | Il se déplace pour chaque changement | 5 000–10 000 FCFA/mois pour la supervision |

---

## 4. Proposition de valeur

> **« Gérez vos routeurs MikroTik, vos abonnés et vos encaissements depuis un navigateur,
> sans WinBox, sans Excel et sans être sur place. »**

Piliers :
1. **Zéro installation** : le routeur se connecte à nous (tunnel WireGuard), pas l'inverse.
2. **Paiement mobile money natif** (Orange Money, Moov Money, Wave, Coris) — le nerf de la guerre local.
3. **Fonctionne en connexion faible** : interface < 300 Ko, mode dégradé, impressions PDF côté serveur.
4. **Souveraineté et langue** : français, FCFA, support WhatsApp, hébergement choisi.

---

## 5. Périmètre du MVP (MoSCoW)

### Must have (v1 — 12 à 16 semaines)
- Multi-tenant : inscription, espaces de travail, rôles (propriétaire, technicien, caissier, lecture seule).
- Onboarding d'un routeur : tunnel WireGuard, création d'un utilisateur API restreint, test de connexion.
- Inventaire : sites, routeurs, interfaces, identité, version RouterOS, statut en ligne/hors ligne.
- Hotspot : profils/forfaits, lots de vouchers (PDF/QR), import/export CSV, suspension/réactivation.
- **RADIUS** : authentification hotspot + comptabilité (Accounting-Start/Interim/Stop).
- Sessions actives : voir, déconnecter (CoA / `active/remove`), consommation temps réel.
- Caisse : vente de vouchers, journal des encaissements, reçus PDF.
- Portail captif personnalisable (logo, couleurs, textes) + achat voucher par mobile money.
- Tableau de bord : CA du jour, sessions actives, routeurs hors ligne, alertes.
- Journal d'audit de toutes les actions sensibles.

### Should have (v1.1)
- Facturation abonnés PPPoE, prorata, relances automatiques, suspension pour impayé.
- Sauvegarde automatique des configurations + diff + restauration.
- Alertes (routeur down, CPU, interface down, quota atteint) + notifications e-mail/WhatsApp.
- Rôles fins, invitations, 2FA.
- API publique + webhooks pour intégrateurs.

### Could have (v2)
- Application mobile React Native pour techniciens (scan QR, diagnostic).
- Prédiction de la consommation / recommandation de forfaits.
- Gestion de stock de matériel, interventions, planning.
- Marketplace de templates de portails captifs.
- Trunk SIP / VoIP billing (autre marché, mêmes briques).

### Won't have (assumé et documenté)
- Routeur matériel / vente de matériel.
- FAI ourselves (revente de bande passante).
- Proxy ou filtrage de contenu utilisateur (responsabilité légale et coût).
- Support RouterOS v6 en dessous de 6.49 (EOL) — à confirmer avec le marché local.
- Comptabilité certifiée / liasse fiscale (on exporte, on ne remplace pas le comptable).

---

## 6. Modèle économique (hypothèses à valider)

| Offre | Cible | Prix indicatif (FCFA/mois) | Inclus |
|---|---|---|---|
| **Découverte** | Test | 0 | 1 routeur, 30 clients, filigrane |
| **Starter** | Cybercafé | 9 500 | 3 routeurs, 300 clients actifs, vouchers illimités |
| **Pro** | Multi-sites | 25 000 | 10 routeurs, 1 500 clients, portail marque blanche, API |
| **Business** | Petit FAI | 75 000 | 50 routeurs, 8 000 clients, facturation, SLA 99,5 % |
| **Enterprise** | > 50 sites | sur devis | Cluster dédié, SSO, hébergement au choix |

Compléments : commission de 3 % sur les ventes de vouchers en ligne (ou 0 % si le client encaisse
lui-même), frais de mise en service (25 000 FCFA, offerts en promo), pack installation à distance.

**Unit economics cible (hypothèse)** : coût d'infrastructure ≈ 60 000 FCFA/mois jusqu'à ~150 sites ;
marge brute > 80 % dès 20 clients payants. Le coût réel est le **support**, pas les serveurs.

> ⚠️ Ces prix sont des hypothèses de travail. Ils doivent être testés par 10 entretiens
> clients avant la première ligne de code (voir `10-checklists.md`).

---

## 7. Concurrence et différenciation

| Acteur | Forces | Faille exploitable |
|---|---|---|
| MikroTik User Manager | Gratuit, intégré | Local à un routeur, pas de multi-site, interface datée, pas de mobile money |
| SPlynx / Sonar | Très complets | Chers en devises, pensés pour l'Europe, support en anglais, facturation en EUR |
| Radius Manager (DMA) | Mature | Windows/VMs, UX ancienne, licence par abonné |
| mkcontroller / TangoWave | Cloud, simple | Peu de billing local, pas de mobile money FCFA |
| Scripts maison + Excel | Gratuit | Fragile, dépend d'une personne, aucune traçabilité |

**Notre créneau** : le **dernier kilomètre administratif** africain — mobile money, FCFA, français,
connexion faible, support WhatsApp, prix mensuel sans engagement, et migration gratuite depuis Excel.

---

## 8. Indicateurs de succès

| Horizon | KPI | Cible |
|---|---|---|
| 90 j | Routeurs connectés (pilotes) | 15 |
| 6 mois | Clients payants / MRR | 20 / 400 000 FCFA |
| 12 mois | MRR / churn mensuel | 1,5 M FCFA / < 3 % |
| Permanent | Disponibilité plateforme | 99,5 % |
| Permanent | Temps d'onboarding d'un routeur | < 15 min, sans intervention à distance |

---

## 9. Risques principaux

| Risque | Impact | Mitigation |
|---|---|---|
| Routeurs derrière CGNAT (4G Orange/Moov) | Injoignables | Tunnel WireGuard initié par le routeur (obligatoire dès le J1) |
| Mot de passe routeur volé | Compromission totale du parc | Chiffrement enveloppe, utilisateur API dédié et restreint, rotation, MFA admin |
| Panne plateforme = clients hors ligne | Perte de confiance | Le routeur garde ses utilisateurs en local (fallback), RADIUS avec cache/repli, SLA clair |
| Dépendance à l'API propriétaire | Blocage technique | Couche d'abstraction `MikroTikGateway` + backend REST et binaire interchangeables |
| Clients qui paient en retard nous-mêmes | Trésorerie | Prélèvement mobile money récurrent, suspension douce, offre annuelle prépayée |
| Réglementation télécom (ARPCE) | Blocage commercial | Nous vendons un **logiciel**, pas de la connectivité ; valider avec un juriste local |
| Données personnelles (CIL / loi locale) | Sanction, réputation | Minimisation, chiffrement, journalisation, politique de conservation (voir `06-securite.md`) |

---

## 10. Décisions à prendre avant de coder

> **Mise à jour du 2026-11-01** — décisions prises avec le porteur du projet :
> - vertical retenu : **A (hotspot) + C (supervision)** ; le FAI/PPPoE (B) passe en V2 ;
> - cible : **tout RouterOS 7** (REST + API binaire en repli dès le départ), 6.49 hors périmètre ;
> - application mobile : **PWA d'abord**, React Native seulement si besoin terrain confirmé.
>
> Restent ouvertes : hébergement, agrégateur de paiement, marque blanche au MVP, SLA.

1. Le vertical : **A seul**, ou **A + C** dès le départ (recommandé) ?
2. Support minimal de RouterOS : 7.x uniquement, ou 6.49 également ? (impacte la couche d'abstraction)
3. Cloud : VPS local (Ouaga/Abidjan) ou Europe (OVH/Hetzner) ? Impacte la latence et la confiance client.
4. Paiement : agrégateur (CinetPay, PayDunya, KkiaPay, FedaPay) ou intégration directe par opérateur ?
5. Marque blanche dès le MVP (portail par tenant) ou plus tard ?
6. Application mobile : PWA d'abord (recommandé) ou React Native d'emblée ?

→ Suivre l'avancement dans `10-checklists.md`.
