# 15 · Tester avec un routeur x86 dans VirtualBox

> **But** : brancher la plateforme sur **ton** routeur RouterOS x86 (VM VirtualBox) en local,
> sans tunnel WireGuard, et vérifier de bout en bout : enrôlement → connexion → sonde → santé.
>
> Public : développeur. Temps de mise en route : 10 à 15 minutes.

---

## 1. Ce qui est supporté

| Élément | Statut |
|---|---|
| RouterOS **7.x** (x86, CHR, hAP, RB) via **API REST** (`www-ssl` ou `www`) | ✅ supporté |
| Certificat **auto-signé** du routeur | ✅ vérification TLS désactivée par défaut |
| Port personnalisé (443, 80, 8080…) et HTTP sans TLS | ✅ |
| Routeur **6.49** (API binaire seule) | ⬜ P3 — repli binaire prévu |
| Routeur **derrière NAT** (VirtualBox « NAT ») | ⚠️ nécessite une redirection de port (voir §6) |

Deux modes de connexion coexistent :

1. **Routeur réel déjà installé** → on saisit ses identifiants (ils sont chiffrés) :
   c'est le mode à utiliser avec ta VM.
2. **Routeur neuf** → on génère un script d'enrôlement (WireGuard + utilisateur API),
   prévu pour le déploiement à distance.

---

## 2. Réseau de la VM (VirtualBox)

Le plus simple : une carte **« Accès par hôte » (host-only)**, qui donne une adresse
joignable depuis ta machine et invisible du réseau local.

| Réglage VirtualBox | Valeur |
|---|---|
| Carte 1 | NAT (pour les mises à jour RouterOS) |
| Carte 2 | **Accès par hôte** — `vboxnet0` |
| Réseau host-only | `192.168.56.0/24` |
| Adresse de la VM | `192.168.56.101/24` |

Sur le routeur :

```
/ip address add address=192.168.56.101/24 interface=ether2 comment="kora host-only"
/ip route add dst-address=0.0.0.0/0 gateway=<passerelle NAT> routing-table=main
```

> Si tu n'as qu'une carte, tu peux aussi garder le mode NAT et ajouter une règle de
> redirection : `Settings → Network → Advanced → Port Forwarding`
> (`127.0.0.1:8443 → 10.0.2.15:443`), puis utiliser `--host 127.0.0.1 --port 8443`.

Vérifie depuis **l'hôte** :

```bash
ping -c 2 192.168.56.101          # la VM répond
nc -vz 192.168.56.101 443         # le service HTTPS est ouvert
```

---

## 3. Configurer RouterOS pour l'API REST

```
# 1. Activer le service REST (RouterOS 7 : fourni par www / www-ssl)
/ip service enable www-ssl
/ip service set www-ssl port=443 address=192.168.56.0/24

# 2. Groupe et utilisateur dédiés à la plateforme
/user group add name=kora policy=read,write,api,rest-api,test,romon,sensitive
/user add name=kora group=kora password='UnMotDePasseLong-2026' comment="Kora SaaS"

# 3. (Recommandé) Ne pas exposer l'API sur l'interface WAN
/ip firewall filter add chain=input in-interface=ether1 protocol=tcp dst-port=443 action=drop \
    comment="pas d'API depuis Internet"
```

> ⚠️ Ne réutilise pas `admin` : la plateforme doit pouvoir être révoquée sans toucher
> à ton compte d'administration. Les identifiants sont stockés chiffrés (AES-256-GCM).

Test manuel immédiat (le `-k` ignore le certificat auto-signé) :

```bash
curl -k -u kora:'UnMotDePasseLong-2026' https://192.168.56.101/rest/system/resource
```

Réponse attendue : un JSON contenant `"version":"7.16.2"`, `"board-name":"x86"`…
Si tu obtiens `401` → mot de passe ou utilisateur incorrect ; `403` → policy
`rest-api` manquante ; `Connexion refusée` → service `www-ssl` désactivé ou filtre.

---

## 4. Tester depuis la plateforme (ligne de commande)

Aucune base de données n'est modifiée : c'est le test le plus rapide.

```bash
cd backend

# HTTPS (par défaut, port 443)
python manage.py probe_router --host 192.168.56.101 --username kora --password 'UnMotDePasseLong-2026'

# HTTP simple (service www, port 80)
python manage.py probe_router --host 192.168.56.101 --username kora --password '…' --http --port 80

# Avec les interfaces
python manage.py probe_router --host 192.168.56.101 --username kora --password '…' --interfaces
```

Sous **Windows**, le script `dev.ps1` fait la même chose (voir
[`docs/17`](17-environnement-windows.md)) :

```powershell
.\dev.ps1 probe -RouterHost 192.168.56.101 -RouterUser kora -RouterPassword "UnMotDePasseLong-2026"
```

Sortie attendue :

```
→ https://192.168.56.101:443/rest/system/resource
✔ x86-kora — RouterOS 7.16.2 (CHR)
  série XXXXXXXX · uptime 2541s · CPU 3% · mémoire 21% · 12 ms
  · ether1 (ether) up
  · ether2 (ether) up
```

Pour **rattacher** ces identifiants à un routeur déjà déclaré dans la console :

```bash
python manage.py probe_router --host 192.168.56.101 --username kora --password '…' \
  --tenant demo-kora --device <uuid-du-routeur>
```

---

## 5. Tester depuis la console (interface web)

1. `make demo` (crée `demo@kora.bf`) puis `make run` et `make console`.
2. Se connecter, aller dans **Routeurs → Ajouter un routeur** :
   nom `CHR x86 · virtualbox`, IP `192.168.56.101`, port `443`, HTTPS coché.
3. Ouvrir la fiche → **Connecter le routeur** → utilisateur `kora` + mot de passe →
   *Enregistrer et tester*.
4. Résultat attendu : bandeau vert « Contact établi en X ms · RouterOS 7.16.2 »,
   statut **En ligne**, cartes CPU / mémoire / uptime, tableau des interfaces.

L'API appelée est la même que celle du CLI :

| Action console | Requête |
|---|---|
| Connexion | `POST /api/v1/auth/token/` |
| Enregistrer les identifiants | `POST /api/v1/devices/{id}/credentials/` |
| Sonde | `POST /api/v1/devices/{id}/test-connection/` |
| Script d'enrôlement | `POST /api/v1/devices/{id}/enroll/` |

---

## 6. Tests automatisés contre ta VM

```bash
# Linux / macOS
cd backend
MIKROTIK_LIVE_HOST=192.168.56.101 MIKROTIK_LIVE_USER=kora \
MIKROTIK_LIVE_PASSWORD='UnMotDePasseLong-2026' pytest -m live -v
```

```powershell
# Windows (PowerShell)
cd backend
$env:MIKROTIK_LIVE_HOST = "192.168.56.101"
$env:MIKROTIK_LIVE_USER = "kora"
$env:MIKROTIK_LIVE_PASSWORD = "UnMotDePasseLong-2026"
..\.venv\Scripts\python -m pytest -m live -v
```

Variantes : `MIKROTIK_LIVE_HTTP=1` (HTTP), `MIKROTIK_LIVE_PORT=8443` (redirection NAT).

Sans ces variables, le test est **ignoré** (`1 skipped`) : la suite reste exécutable
partout, y compris en intégration continue.

---

## 7. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `Routeur injoignable (URLError)` | VM éteinte, mauvaise IP, carte NAT | vérifier `ping`, passer en host-only |
| `timeout après 10 s` avec NAT | port non redirigé | ajouter une règle Port Forwarding |
| `HTTP 401` | utilisateur ou mot de passe | recréer l'utilisateur, tester avec `curl -u` |
| `HTTP 403` | policy `rest-api` absente | `/user group set kora policy=read,write,api,rest-api,test` |
| `HTTP 404` sur `/rest/...` | RouterOS 6.x | passer en 7.x (l'API REST n'existe pas en 6.49) |
| `certificate verify failed` | certificat auto-signé | `MIKROTIK_VERIFY_TLS=0` (défaut) |
| Page blanche console | API arrêtée | `make run` puis recharger (`make console`) |

Journal côté plateforme : les erreurs de sonde sont **attendues** et journalisées, le
routeur passe simplement en `unreachable` — aucune exception ne remonte au worker.

---

## 8. Ce que ce test valide (et ce qu'il ne valide pas)

Validé avec ta VM : authentification REST, lecture de l'identité et des ressources,
compteurs d'interface, persistance de la santé, statut en ligne/hors ligne, chiffrement
des identifiants, isolation multi-tenant.

Non validé à ce stade (prévu en P3/P4) : création d'utilisateurs hotspot par l'API,
provisionnement des vouchers, tunnel WireGuard automatique, repli API binaire 6.49.
