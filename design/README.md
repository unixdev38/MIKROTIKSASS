# Maquettes — Kora

Prototype **statique** de la console et du portail captif. Aucune dépendance externe
(pas de CDN, pas de police distante), aucune donnée réelle.

## Voir les maquettes

```bash
python3 design/build.py                        # génère design/dist/
python3 -m http.server 8000 -d design/dist     # http://localhost:8000
```

Point d'entrée : **`index.html`** (couverture cliquable vers les 13 écrans).

## Structure

```
design/
├─ build.py          # génère les pages dans dist/
├─ kit.py            # icônes SVG, graphiques, QR, coquille de page, navigation
├─ pages_core.py     # tableau de bord, parc, fiche routeur, sessions
├─ pages_sales.py    # forfaits, vouchers, caisse, équipe & audit
├─ pages_misc.py     # connexion, enrôlement, portail, design system, index
├─ styles.css        # design system : jetons + composants (source de vérité visuelle)
├─ app.js            # micro-interactions (copier, onglets, sélection, switch)
└─ dist/             # pages générées — ne pas éditer à la main
```

## Règles

- **`styles.css` est la source de vérité** des couleurs, espacements et composants.
  La marque blanche ne doit toucher que le bloc `:root`.
- Les pages sont générées : toute correction se fait dans `*.py` puis `build.py`.
- Pas d'ajout de dépendance JS/CSS sans discussion : le prototype doit rester ouvrable hors ligne.
- Les QR codes sont **factices** (déterministes, non scannables) — c'est volontaire.

## Limites assumées

- Seul l'état « nominal » est maquetté : les états vide / chargement / erreur sont décrits dans
  [`docs/12-design-system.md`](../docs/12-design-system.md).
- Aucun appel réseau : les actions ne font rien (sauf le bouton « Encaisser » et l'attente d'enrôlement,
  simulés en JS pour la démonstration).
- Le nom « Kora » est un nom de travail.
