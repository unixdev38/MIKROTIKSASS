# ADR 0004 — RADIUS pour l'AAA + utilisateurs locaux sur le routeur (résilience)

- **Statut** : accepté (à valider en laboratoire, cf. §Conséquences)
- **Date** : 2026-11-01

## Contexte

Deux approches sont possibles pour authentifier les clients hotspot/PPPoE :

- **A. Tout par l'API** : la plateforme crée des utilisateurs sur le routeur, le routeur authentifie
  en local. Simple, mais la plateforme devient un point de passage pour chaque ajout, et la
  comptabilité temps réel est approximative.
- **B. Tout par RADIUS** : le routeur interroge FreeRADIUS à chaque connexion. Temps réel et
  facturation précis, mais **si RADIUS tombe, plus personne ne peut se connecter** — et un incident
  chez nous devient un incident chez le client.

Le contexte local (coupures électriques, liens instables) impose de privilégier la continuité de
service chez le client.

## Décision

**Approche hybride (C)** :

1. L'utilisateur/voucher est créé **localement sur le routeur** (`/ip/hotspot/user`, `/ppp/secret`)
   avec ses limites (`limit-uptime`, `limit-bytes-total`, profil de débit).
2. Il est **aussi** présent dans RADIUS (source de vérité côté plateforme) pour l'audit, la
   facturation, les quotas dynamiques et la coupure à distance (CoA).
3. Le profil hotspot/PPP est configuré avec `use-radius=yes` : RADIUS est consulté, mais les
   utilisateurs locaux restent une voie de secours.
4. La réconciliation quotidienne compare les deux sources et signale les écarts.

## Conséquences

**Positives**
- Une panne de la plateforme ou de RADIUS **ne coupe pas** les clients existants ni les connexions
  avec un voucher encore valide.
- La comptabilité reste exploitable via `Accounting-Interim-Update`.
- Migration et support facilités : on peut toujours intervenir localement sur le routeur.

**Négatives / à valider**
- Duplication d'état (routeur + base) → nécessite la réconciliation et le marquage `saas:` sur les objets.
- Les quotas appliqués localement et ceux connus par la plateforme peuvent diverger de quelques minutes.
- **Point à valider en laboratoire** : le comportement exact de RouterOS quand RADIUS ne répond pas
  (`use-radius=yes` + utilisateurs locaux présents). Si le routeur rejette au lieu de basculer, la
  parade est un profil hotspot dédié « secours » et une documentation honnête du SLA.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| RADIUS exclusif | Une panne côté plateforme coupe des clients payants : inacceptable commercialement |
| API/locale exclusive | Pas de facturation fiable, pas de coupure à distance, polling coûteux |
| User Manager MikroTik sur chaque routeur | Local à un routeur, aucune vue consolidée, pas de multi-site |
