# ADR 0005 — Le routeur initie un tunnel WireGuard vers la plateforme

- **Statut** : accepté
- **Date** : 2026-11-01

## Contexte

La majorité des routeurs clients n'ont **pas d'IP publique fixe** : connexions 4G derrière CGNAT,
ADSL avec IP dynamique, double NAT chez un revendeur. Or notre plateforme doit joindre l'API de
chaque routeur (8729/REST). Ouvrir les ports de management sur Internet est exclu (risque majeur :
des milliers de routeurs MikroTik compromis chaque année via des services exposés).

## Décision

Chaque routeur établit un **tunnel WireGuard sortant** vers un concentrateur de la plateforme
(`10.66.0.0/16`, un /24 par tenant, une IP par routeur). L'API n'est joignable **que** par ce tunnel,
avec `address=10.66.0.0/24` sur le service `api-ssl`.

- Clés générées par la plateforme à l'enrôlement, uniques par routeur, révocables.
- `persistent-keepalive=25s` pour traverser les NAT.
- `api`, `www`, `telnet`, `ftp`, `ssh` désactivés ; `winbox` limité au tunnel.
- Repli documenté si le client refuse le tunnel : IP publique + allowlist d'IP + heartbeat sortant
  (mode « pull », moins fiable, proposé uniquement aux routeurs à IP fixe).

## Conséquences

**Positives**
- Fonctionne derrière CGNAT et double NAT : couvre le marché réel.
- Surface d'attaque quasi nulle : aucun port de management exposé sur Internet.
- Le mode « en ligne/hors ligne » se déduit du tunnel et du heartbeat.
- Le tunnel peut aussi servir de secours d'accès pour le technicien (option future).

**Négatives**
- Un composant de plus à exploiter (concentrateur WireGuard, table des pairs).
- Le client doit accepter une modification de configuration sur son routeur (script fourni).
- Nécessite RouterOS 7.1+ ; RouterOS 6 doit passer par IPsec/L2TP (support dégradé).
- Le débit du tunnel peut être limité par le CPU du routeur : on ne l'utilise pas pour du trafic
  client, uniquement pour le management.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| Ports API/REST ouverts sur Internet | Risque de compromission inacceptable, non défendable devant un client |
| DDNS MikroTik Cloud | Ne résout pas le CGNAT de tous les opérateurs, dépend d'un tiers |
| Agent installé sur un PC local | Dépend d'une machine allumée, complexité de support |
| OpenVPN sur le routeur | Plus lourd, plus lent, configuration plus fragile que WireGuard sur RouterOS 7 |
| Reverse SSH maintenu par nous | Fragile, gestion de clés complexe, moins performant |
