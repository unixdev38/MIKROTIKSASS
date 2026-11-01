# 02 — Intégration MikroTik / RouterOS : référence technique

> Statut : **référence de conception** · Dernière mise à jour : 2026-11-01
> Sources : documentation officielle RouterOS (API, REST API, User Manager, Hotspot, RADIUS).

---

## 1. Les 4 canaux de communication disponibles

| Canal | Port | Sens | Temps réel | Fiabilité | Usage dans notre SaaS |
|---|---|---|---|---|---|
| **API binaire** | 8728 (clair) / 8729 (TLS) | Nous → routeur | Oui, via `listen` | Bonne, sensible à la latence | Provisioning, inventaire, sessions |
| **REST API** (ROS ≥ 7.1) | 443 (service `www-ssl`) | Nous → routeur | Non | Bonne, traversée proxy facile | CRUD alternatif, environnements filtrés |
| **RADIUS** | UDP 1812/1813, CoA 3799 | Routeur → nous | Oui (comptabilité) | Critique | Authentification et consommation |
| **Scripts routeur** (`/tool fetch`) | 443 sortant | Routeur → nous | Quasi temps réel | Bonne | Heartbeat, événements, alerte |

**Règle** : le canal RADIUS porte l'authentification et la comptabilité ; l'API ne sert **que** au
contrôle. Un SaaS qui authentifie chaque client via l'API binaire s'écroule au-delà de quelques
centaines de connexions par minute.

---

## 2. L'API binaire en bref (ce qu'il faut savoir pour ne pas se tromper)

### 2.1 Encodage
- Une *phrase* (sentence) = une suite de *mots* (words) terminée par un mot de longueur **zéro**.
- Chaque mot commence par sa longueur, encodée sur 1 à 5 octets (bit de poids fort = continuation).
- Types de mots :

| Préfixe | Type | Exemple |
|---|---|---|
| *(aucun)* | Commande | `/ip/hotspot/user/add` |
| `=` | Attribut | `=name=client01`, `=limit-uptime=1h` |
| `?` | Requête (filtre, ordre significatif) | `?name=client01` |
| `?#` | Opérations de pile (`|`, `!`, `&`, …) | `?#|` (OR) |
| `.` | Attribut API (`tag`) | `.tag=42` |

- Réponses : `!re` (donnée), `!done` (fin), `!trap` (erreur applicative, champ `=message=`),
  `!fatal` (fermeture imminente), `!empty` (aucune donnée, ROS ≥ 7.18).
- `tag` permet de multiplexer plusieurs commandes sur une même connexion ; utile pour corréler
  les réponses, **indispensable** si on ne sérialise pas les commandes.

### 2.2 Login
Depuis RouterOS 6.43 : `"/login" =name=<user> =password=<pass>` puis `!done`.
Le mot de passe circule **en clair** → le TLS (8729) est obligatoire, pas optionnel.

### 2.3 Commandes principales

| Commande | Rôle | Remarque |
|---|---|---|
| `/…/print` | Lister | Toujours avec `=.proplist=` et `?` filtres |
| `/…/add` | Créer | Renvoie `=ret=<.id>` |
| `/…/set` | Modifier | Cibler par `.id` ou `=numbers=` |
| `/…/remove` | Supprimer | `=numbers=` accepte une liste |
| `/…/enable`, `/…/disable` | Activer/désactiver | Préférer à `set =disabled=yes` |
| `/…/move` | Réordonner | Important pour les règles firewall et les queues |
| `/…/listen` | Écoute des changements | Ne termine jamais → `/cancel` |
| `/cancel` | Annuler | `=tag=` ou tout |
| `/system/reboot` | Redémarrer | À protéger (politique `policy`) |

### 2.4 Pièges à documenter dès maintenant

| Piège | Conséquence | Parade |
|---|---|---|
| Pas de transactions | Une config à moitié appliquée | Tâches idempotentes + réconciliation (`desired state`) |
| Ordre des attributs non garanti | Parsing fragile | Ne jamais dépendre de l'ordre |
| `.proplist` absent = tout renvoyer | Routeur saturé, réponses énormes | `.proplist` systématique |
| `print` sans filtre sur 10 000 entrées | Timeout, CPU 100 % | Pagination par préfixe / filtres `?` |
| `listen` occupe une connexion | Fuite de sockets | 1 connexion dédiée par écoute, re-souscription après reconnexion |
| `.dead=yes` sur suppression | Objets fantômes en base | Traiter `.dead` comme un événement de suppression |
| Timeout réseau silencieux | Tâches zombies | Timeout 10 s, 3 tentatives, circuit breaker |
| `remove` d'un `.id` inexistant | `!trap` | Traiter `!trap` comme « déjà fait » si message = not found |
| Mot de passe API dans les logs | Fuite | Filtre de logs, jamais d'URL avec credentials |

---

## 3. Configuration à appliquer sur chaque routeur client

Script **idempotent**, à exécuter une seule fois par le technicien (copier/coller dans le terminal
WinBox ou via l'importateur `/import`). Les valeurs `<…>` sont générées par la plateforme.

```rsc
# ---- MIKROTIK SAAS — script d'enrôlement v1 (RouterOS 7.x) ----
# 1. Identité (facilite le support)
/system identity set name="<site>-<device>"
/system note set show-at-login=no note="Géré par <marque> — ne pas supprimer la config 'saas'"

# 2. Interface de management dédiée (tunnel sortant, fonctionne derrière CGNAT)
/interface wireguard
add name=wg-saas listen-port=51820 private-key="<private-key>" comment="saas:mgmt"
/interface wireguard peers
add interface=wg-saas public-key="<cloud-public-key>" endpoint-address=<cloud-vpn-ip> \
    endpoint-port=51820 allowed-address=10.66.0.0/24 persistent-keepalive=25s comment="saas:peer"
/ip address
add address=10.66.<tenant>.<device>/24 interface=wg-saas comment="saas:mgmt-ip"

# 3. Utilisateur API dédié, moindre privilège, restreint au réseau de management
/user group
add name=saas-api policy=api,read,write,rest-api,test comment="saas:group"
/user
add name=saas-api group=saas-api password="<mot-de-passe-généré>" \
    address=10.66.0.0/24 comment="saas:api-user"

# 4. Services : on ferme tout ce qui n'est pas nécessaire
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set api disabled=yes
set api-ssl disabled=no address=10.66.0.0/24
set winbox address=10.66.0.0/24
set ssh disabled=yes

# 5. Certificat pour api-ssl (auto-signé, épinglé côté plateforme)
/certificate
add name=saas-cert common-name=saas-api days-valid=3650 key-usage=tls-server
/ip service set api-ssl certificate=saas-cert

# 5bis. REST (optionnel, RouterOS >= 7.1) : nécessite le service www-ssl
/ip service set www-ssl disabled=no address=10.66.0.0/24 certificate=saas-cert

# 6. Heartbeat sortant (la plateforme sait que le routeur est vivant)
/system script
add name=saas-heartbeat source={
  /tool fetch url="https://<api>/hooks/device/<device-uuid>/heartbeat" \
    http-method=post http-header-field="X-Device-Token:<token>" \
    http-data=("{\"ver\":\"" . [/system resource get version] . "\",\"up\":\"" . [/system resource get uptime] . "\"}") \
    check-certificate=yes keep-result=no
}
/system scheduler
add name=saas-heartbeat interval=1m on-event=saas-heartbeat comment="saas:heartbeat"
```

> ⚠️ **Ne jamais** exposer `api`, `winbox`, `ssh` ou `www` sur Internet. Le tunnel est le seul chemin.
> Le script doit être testé sur CHR **et** sur un routeur réel avant d'être livré aux clients.

### Variante sans WireGuard (repli)
Si le client refuse le tunnel : `api-ssl` ouvert avec `address=<IP publique de la plateforme>` + le
routeur initie le heartbeat et reçoit les ordres via une file en attente (« pull »). Moins bon, mais
utilisable pour les routeurs à IP publique fixe.

---

## 4. API REST (RouterOS ≥ 7.1)

```
GET    /rest/ip/hotspot/user            → liste JSON
PUT    /rest/ip/hotspot/user            → création (attention : PUT, pas POST)
PATCH  /rest/ip/hotspot/user/<id>       → modification
DELETE /rest/ip/hotspot/user/<id>       → suppression
POST   /rest/ip/hotspot/user/print      → commande avec paramètres/requêtes
```

- Nécessite le service `www-ssl` actif **et** un certificat installé.
- Authentification HTTP Basic (utilisateur RouterOS).
- Sélection de champs : paramètre `.proplist`. Requêtes : paramètres préfixés par `?`.
- En-tête `Accept: application/json` (ou `application/ojson`).
- **Pas de `listen`** : le REST ne remplace pas l'API binaire pour le temps réel.

**Décision** : REST comme backend **préféré** pour le CRUD (plus simple, plus sûr, pas de dépendance
binaire), API binaire pour l'écoute et RouterOS 6. Voir `09-adr/0002`.

---

## 5. Couche d'abstraction `MikroTikGateway`

```
MikroTikGateway (interface)
├── get_system_info(device) -> SystemInfo
├── list_hotspot_users(device) -> list[HotspotUser]
├── upsert_hotspot_user(device, user) -> Result
├── remove_hotspot_user(device, id_or_name) -> Result
├── list_hotspot_active(device) -> list[ActiveSession]
├── disconnect_session(device, session_id) -> Result
├── list_ppp_secrets / upsert_ppp_secret / disable_secret
├── list_interfaces(device) -> list[Interface]  (stats incluses)
├── list_queues / upsert_queue
├── add_to_address_list / remove_from_address_list
├── backup_config(device) -> bytes
├── listen(device, path) -> AsyncIterator[Event]   (binaire uniquement)
└── healthcheck(device) -> DeviceHealth
```

Deux implémentations : `RestBackend` (httpx) et `BinaryBackend` (librouteros). Un `FakeBackend`
alimenté par des fixtures CHR permet de tester toute la plateforme **sans routeur**.

### 5.1 Conventions de nommage et de marquage

Chaque objet créé sur un routeur porte un commentaire **unique et traçable** :

```
comment=saas:<tenant_short_id>:<entity_type>:<entity_uuid>
ex.  comment=saas:bf01:hotspot_user:8f14e45f-ceea-467a
```

Avantages :
- réconciliation possible (`/print` puis diff avec nos UUID) ;
- nettoyage sûr lors d'une suppression de tenant ;
- support : on retrouve immédiatement l'origine d'un objet ;
- aucune collision avec les objets créés manuellement par le client (qui n'ont pas le préfixe `saas:`).

### 5.2 Réconciliation plutôt qu'impératif

| Approche | Problème | Notre choix |
|---|---|---|
| « J'envoie `add`, si échec j'abandonne » | Dérive irréversible, doublons | ❌ |
| « Je calcule l'état désiré et je corrige l'écart » | Plus de code, mais auto-réparateur | ✅ |

Cycle : `DesiredState` (base) → `fetch actual` (routeur) → `plan` (create/update/delete) →
`apply` (commandes) → `verify`. Le plan est journalisé, ce qui rend les incidents diagnostiquables.

### 5.3 Performance

- 1 session de commandes **persistante** par routeur, protégée par un verrou Redis (`lock:device:<id>`).
- `.proplist` toujours renseigné ; jamais de `print` massif.
- Métriques d'interface : lire les compteurs `rx-byte`/`tx-byte` d'un `/interface/print =stats=`
  et calculer les deltas côté plateforme (bien moins coûteux que `monitor-traffic`).
- Polling par défaut : 60 s (configurable par tenant) ; 5 min pour les données non critiques.
- Sur routeur d'entrée de gamme (hAP lite, 32 Mo de RAM), viser **≤ 1 commande/s en pointe**.

---

## 6. RADIUS : le vrai moteur du billing

### 6.1 Ce que le routeur envoie

| Paquet | Moment | Attributs utiles |
|---|---|---|
| `Access-Request` | À chaque connexion | `User-Name`, `Calling-Station-Id` (MAC), `NAS-IP-Address`, `NAS-Port-Id` |
| `Accounting-Start` | Début de session | `Acct-Session-Id`, `Framed-IP-Address` |
| `Accounting-Interim-Update` | Périodique (5 min) | `Acct-Input-Octets`, `Acct-Output-Octets`, `Acct-Session-Time` |
| `Accounting-Stop` | Fin | idem, totaux définitifs |

### 6.2 Ce que nous renvoyons (`Access-Accept`)

| Attribut | Effet |
|---|---|
| `Session-Timeout` | Durée max de la session |
| `Idle-Timeout` | Déconnexion si inactif |
| `Acct-Interim-Interval` | Fréquence des updates (300 s) |
| `Mikrotik-Rate-Limit` (VSA 14988) | `"2M/2M"` → 2 Mbit/s descendant / montant |
| `Mikrotik-Total-Limit` | Quota total en octets |
| `Mikrotik-Address-List` | Placement dans une liste (ex. `PAID`) |
| `Mikrotik-Recv-Limit` / `Xmit-Limit` | Quotas séparés |

### 6.3 Déconnexion à distance

- **PPPoE** : `Disconnect-Message` (RFC 5176) sur UDP 3799 — supporté.
- **Hotspot** : `Disconnect` à valider en labo ; repli fiable = `/ip/hotspot/active/remove` via l'API.
- Toujours prévoir un **double chemin** : CoA *et* API, avec le même effet attendu.

### 6.4 Schéma de base RADIUS (FreeRADIUS + Django)

- `radcheck` — identifiants (`Cleartext-Password`), généré depuis nos vouchers/abonnés ;
- `radreply` — attributs de réponse ;
- `radgroupcheck` / `radgroupreply` — gabarits par offre ;
- `radacct` — sessions (alimentée par FreeRADIUS) → **notre source de vérité pour la consommation** ;
- `radusergroup` — rattachement utilisateur → offre.

Notre base applicative reste maîtresse ; FreeRADIUS lit ces tables (et peut appeler notre API pour
les cas dynamiques : quota, solde, date d'expiration).

### 6.5 Résilience : le routeur doit continuer à fonctionner sans nous

Pattern retenu (voir ADR `0004`) :
1. Le voucher/abonné existe **en local sur le routeur** (`/ip/hotspot/user`) **et** dans RADIUS.
2. Les limites `limit-uptime` / `limit-bytes-total` sont posées **localement** → le routeur applique
   le forfait même si notre plateforme est injoignable.
3. RADIUS sert à l'audit, au temps réel, à la facturation et au pilotage fin (CoA, quotas dynamiques).
4. En cas de panne RADIUS, le routeur retombe sur l'utilisateur local (config `use-radius=yes` +
   utilisateurs locaux présents). **À valider impérativement sur CHR** avant de le promettre aux clients.

C'est le compromis qui donne le meilleur rapport simplicité/résilience pour un MVP.

---

## 7. Capacités gérées via l'API (matrice)

| Domaine | Chemin RouterOS | Lecture | Écriture | Priorité MVP |
|---|---|---|---|---|
| Identité / ressources | `/system/identity`, `/system/resource` | ✅ | ✅ | **P0** |
| Interfaces + compteurs | `/interface` | ✅ | ✅ | **P0** |
| Utilisateurs hotspot | `/ip/hotspot/user` | ✅ | ✅ | **P0** |
| Sessions hotspot | `/ip/hotspot/active` | ✅ | ✅ (remove) | **P0** |
| Profils hotspot | `/ip/hotspot/profile`, `/ip/hotspot/user/profile` | ✅ | ✅ | **P0** |
| Secrets PPP | `/ppp/secret`, `/ppp/profile`, `/ppp/active` | ✅ | ✅ | P1 |
| Files d'attente | `/queue/simple`, `/queue/tree` | ✅ | ✅ | P1 |
| Listes d'adresses (blocage) | `/ip/firewall/address-list` | ✅ | ✅ | P1 |
| DHCP | `/ip/dhcp-server`, `/ip/dhcp-server/lease` | ✅ | ✅ | P1 |
| Firewall / NAT | `/ip/firewall/filter`, `/ip/firewall/nat` | ✅ | ⚠️ risqué | P2 (lecture) |
| Sans-fil | `/interface/wireless`, `/interface/wifi` | ✅ | ⚠️ | P2 |
| Sauvegarde config | `/system/backup/save`, `/export` | ✅ | ✅ | **P1** |
| Mise à jour firmware | `/system/package/update`, `/system/reboot` | ✅ | ⚠️ opt-in | P2 |
| Journaux | `/log` | ✅ | — | P2 |
| Scripts / planificateur | `/system/script`, `/system/scheduler` | ✅ | ⚠️ | P2 (uniquement les nôtres) |

Légende : ✅ supporté · ⚠️ possible mais à encadrer (validation, sauvegarde préalable, confirmation UI).

**Ce qui n'est pas possible / pas raisonnable** : transactions, notifications webhook natives (il faut
des scripts), lecture du portail captif, contrôle du trafic client sans queues ni RADIUS, gestion de
matériel non-MikroTik.

---

## 8. Matrice de compatibilité RouterOS

| Fonction | 6.49 (LTS v6) | 7.1 – 7.10 | 7.11+ | 7.18+ |
|---|---|---|---|---|
| API binaire 8728/8729 | ✅ | ✅ | ✅ | ✅ |
| REST `/rest` | ❌ | ✅ | ✅ | ✅ |
| `listen` | ✅ | ✅ | ✅ | ✅ |
| `rest-api` policy | ❌ | ✅ | ✅ | ✅ |
| WireGuard | ❌ (IPsec/L2TP) | ✅ | ✅ | ✅ |
| Réponse `!empty` | ❌ | ❌ | ❌ | ✅ |
| User Manager v7 | ❌ (v6) | ✅ (nouveau paquet) | ✅ | ✅ |
| CoA / Disconnect | ✅ (PPPoE) | ✅ | ✅ | ✅ |

Politique proposée : **support officiel 7.11+**, support « best effort » 7.1–7.10, **6.49 uniquement
sur demande** (backend binaire, sans REST, sans WireGuard → tunnel IPsec ou IP publique).

---

## 9. Bibliothèques et dépendances

| Bibliothèque | Type | Points forts | Limites |
|---|---|---|---|
| **`librouteros`** | binaire, sync | Maintenue, `.proplist`, typage, tests, accès bas niveau au protocole (donc `listen` possible — **à valider** en labo) | Pas de REST, sync (à exécuter en worker) |
| `RouterOS-api` (LaiArturs) | binaire, sync | Très répandue, API simple | Orientée v6, streaming limité |
| `rosrestpy` | REST, async | Léger, moderne | Couverture partielle, projet jeune |
| `httpx` + client maison | REST | Contrôle total, zéro dépendance exotique | À écrire et tester (~300 lignes) |
| `pyrad` | RADIUS | Client/serveur complet, CoA | Bas niveau |

**Recommandation** : interface maison + `librouteros` (binaire) + `httpx` (REST). Épingler les
versions, encapsuler dans un adaptateur, et couvrir par des tests contractuels contre des fixtures
enregistrées depuis un CHR.

---

## 10. Sécurité de l'intégration

| Contrôle | Mise en œuvre |
|---|---|
| Transport | API **uniquement** via WireGuard, `api-ssl` (8729), certificat épinglé |
| Identité | 1 utilisateur API par routeur, mot de passe aléatoire (≥ 24 caractères), groupe restreint |
| Stockage | Chiffrement enveloppe (AES-256-GCM/Fernet), clé de chiffrement (KEK) hors base |
| Rotation | Rotation à la demande, à la résiliation, et après tout incident |
| Réseau | Aucune exposition publique des ports 8728/8729 ; `address=` restreint au sous-réseau VPN |
| Audit | Chaque commande envoyée est journalisée (routeur, commande, acteur, résultat, durée) |
| Limitation | Token bucket par routeur et par tenant ; blocage si > N erreurs d'auth |
| Détection | Alerte si changement de version, d'identité, d'utilisateur API ou de config hors plateforme |
| Destruction | À la résiliation : suppression du tenant → purge des secrets, révocation du pair WireGuard |

---

## 11. Plan de validation technique (à faire **avant** le développement produit)

1. Monter 3 CHR : `7.11`, `7.18`, `6.49` (QEMU/Proxmox ou conteneur privilégié).
2. Écrire un script de test qui se connecte à chacun et vérifie : login, `print` avec `.proplist`,
   `add`/`set`/`remove`, `listen`, `!trap`, coupure réseau en cours de commande.
3. Simuler un routeur derrière un NAT (WireGuard sortant) et valider la latence et la reconnexion.
4. Monter FreeRADIUS + un hotspot CHR : valider `Access-Accept`, `Interim-Update`, quotas,
   `Session-Timeout`, et le comportement **quand RADIUS est coupé** (les utilisateurs locaux
   prennent-ils le relais ?).
5. Tester un vrai routeur d'entrée de gamme (hAP lite / hAP ac²) : CPU pendant un `print` de 500
   utilisateurs, comportement avec 30 sessions actives, mémoire.
6. Consigner chaque résultat dans `docs/11-journal-de-validation.md` (à créer au premier test).

**Aucun engagement commercial ne doit être pris avant l'étape 4.**
