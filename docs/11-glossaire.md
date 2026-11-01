# 11 — Glossaire

> Pour que toute l'équipe (dev, commercial, support) parle la même langue.

## Réseau et MikroTik

| Terme | Définition |
|---|---|
| **RouterOS** | Système d'exploitation des routeurs MikroTik. Version actuelle : 7.x (branche 6.x historique). |
| **CHR** | *Cloud Hosted Router* : RouterOS en machine virtuelle. Licence gratuite plafonnée à 1 Gbit/s — idéal pour le laboratoire. |
| **Hotspot** | Portail captif RouterOS : l'utilisateur doit s'authentifier avant d'accéder à Internet. |
| **Portail captif** | Page web affichée avant l'accès réseau (login, achat, conditions). |
| **Voucher** | Code d'accès prépayé (souvent imprimé ou envoyé par WhatsApp), valable une durée ou un volume. |
| **PPPoE** | Protocole d'accès Internet avec identifiant/mot de passe, courant chez les FAI (fibre, radio). |
| **CPE** | Équipement chez le client (box, routeur, antenne). |
| **Queue** | File d'attente RouterOS servant à limiter le débit (`/queue/simple`, `/queue/tree`). |
| **Address-list** | Liste d'adresses IP utilisée par le pare-feu (blocage, autorisation, marquage). |
| **`.id`** | Identifiant interne d'un objet RouterOS (ex. `*1A`), utilisé pour modifier/supprimer. |
| **`listen`** | Commande API qui diffuse les changements d'une liste en temps réel jusqu'à annulation. |
| **REST API** | Interface HTTP/JSON de RouterOS 7 (`/rest`), nécessite `www-ssl`. |
| **CGNAT** | NAT opérateur : plusieurs abonnés partagent une IP publique → le routeur n'est pas joignable depuis Internet. |
| **WireGuard** | VPN moderne, léger, natif dans RouterOS 7.1+. Utilisé pour le tunnel de management. |
| **NAT** | Traduction d'adresses ; « double NAT » = deux routeurs qui translated → problèmes de ports. |
| **Firmware / RouterBOOT** | Micro-logiciel de démarrage du matériel MikroTik, distinct de RouterOS. |

## Authentification et facturation

| Terme | Définition |
|---|---|
| **RADIUS** | Protocole standard d'authentification, d'autorisation et de comptabilité (AAA) pour l'accès réseau. |
| **AAA** | *Authentication, Authorization, Accounting*. |
| **NAS** | *Network Access Server* : ici, le routeur MikroTik qui interroge RADIUS. |
| **FreeRADIUS** | Serveur RADIUS open source, référence du marché. |
| **CoA / Disconnect** | *Change of Authorization* : ordre envoyé au NAS pour modifier ou couper une session en cours (RFC 5176). |
| **VSA** | *Vendor-Specific Attribute* : attribut propriétaire dans RADIUS (MikroTik = 14988). Ex. `Mikrotik-Rate-Limit`. |
| **Accounting Interim** | Message RADIUS périodique donnant la consommation en cours de session. |
| **User Manager** | Serveur RADIUS intégré à RouterOS (paquet `user-manager`), local à un routeur. |
| **Quota** | Limite de volume (`data_limit_bytes`) ou de durée appliquée à un forfait. |
| **Prorata** | Facturation au prorata du temps restant dans la période. |
| **Dunning** | Série de relances automatiques avant suspension pour impayé. |
| **Mobile money** | Paiement par portefeuille électronique (Orange Money, Moov Money, Wave, Coris). |
| **Agrégateur** | Prestataire qui unifie plusieurs moyens de paiement (CinetPay, PayDunya, KkiaPay…). |
| **USSD push** | Demande de validation envoyée sur le téléphone du payeur. |

## Produit et exploitation

| Terme | Définition |
|---|---|
| **Tenant** | Client de notre SaaS (une entreprise), avec ses données isolées. |
| **Multi-tenant** | Une seule instance applicative servant plusieurs tenants de façon cloisonnée. |
| **RLS** | *Row Level Security* PostgreSQL : filtrage des lignes par le moteur, selon le tenant courant. |
| **Plan de contrôle** | Ce que nous pilotons : configuration, abonnés, facturation. |
| **Plan de données** | Le trafic des utilisateurs finaux — **hors de notre plateforme**. |
| **Réconciliation** | Comparer l'état désiré (base) et l'état réel (routeur) puis corriger les écarts. |
| **Idempotence** | Rejouer une opération produit le même résultat (pas de doublon). |
| **Outbox** | Table d'événements à publier, écrite dans la même transaction que la donnée (fiabilité des webhooks). |
| **SLA** | Engagement de niveau de service (ex. 99,5 % de disponibilité). |
| **RTO / RPO** | Temps de reprise cible / perte de données maximale acceptable. |
| **SLO** | Objectif interne de niveau de service, mesuré en continu. |
| **Runbook** | Procédure pas à pas pour traiter un incident connu. |
| **Post-mortem** | Analyse sans blâme après incident, avec actions correctives. |
| **MRR / Churn** | Revenu récurrent mensuel / taux de perte de clients. |
| **FCFA / XOF** | Franc CFA (Afrique de l'Ouest), sans décimales ; parité fixe 1 EUR = 655,957 XOF. |
| **ARPCE** | Autorité de régulation des communications électroniques et des postes (Burkina Faso). |
| **CIL** | Commission de l'informatique et des libertés (protection des données, Burkina Faso). |
