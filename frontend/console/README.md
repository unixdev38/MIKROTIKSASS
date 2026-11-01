# Console — React + Vite

Interface de gestion du parc : connexion JWT, tableau de bord, routeurs, fiche routeur
(sonde, enrôlement, identifiants réels), réglages.

```bash
npm install
npm run dev     # http://localhost:5173, proxy /api → http://127.0.0.1:8001
npm run build   # vérification de production (dist/)
```

## Principes

- **Aucune logique métier** : l'interface affiche ce que l'API renvoie et déclenche des
  actions (`/test-connection/`, `/enroll/`, `/credentials/`).
- **Session** : jetons dans `localStorage`, renouvellement automatique du jeton d'accès
  sur une réponse `401`, déconnexion = révocation du refresh token côté serveur.
- **Erreurs** : toute réponse `problem+json` est traduite en message lisible
  (`detail`, `title` ou erreurs de champ).
- **Routage** : `HashRouter`, donc aucun réglage serveur (fonctionne derrière n'importe
  quel hébergement statique).

## Écrans

| Route | Rôle |
|---|---|
| `#/` | indicateurs du parc, derniers routeurs |
| `#/devices` | liste, ajout d'un routeur (et de son site) |
| `#/devices/:id` | fiche : état, santé, interfaces, sonde, enrôlement, identifiants |
| `#/settings` | session, espaces, aide « routeur VirtualBox » |

Compte de démonstration : `demo@kora.bf` / `demo-mot-de-passe-2026` (`make demo`).
