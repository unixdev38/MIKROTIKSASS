# 12 — Design system et maquettes

> Statut : **maquettes v1 (prototype cliquable)** · Dernière mise à jour : 2026-11-01
> Fichiers : `design/` (sources) → `design/dist/` (pages générées)
> Regénérer : `python3 design/build.py` · Servir : `python3 -m http.server 8000 -d design/dist`

---

## 1. Ce qui a été produit

| # | Écran | Fichier | Objectif |
|---|---|---|---|
| 1 | Couverture / index | `index.html` | Vue d'ensemble cliquable des maquettes |
| 2 | Connexion | `login.html` | Entrée dans la console (2FA prévue) |
| 3 | Tableau de bord | `dashboard.html` | Recette, sessions, parc, alertes, encaissements |
| 4 | Parc de routeurs | `devices.html` | Inventaire filtrable, statut, version, disque |
| 5 | Fiche routeur | `device.html` | Santé, interfaces, trafic, événements, maintenance |
| 6 | Enrôlement | `enroll.html` | Assistant 4 étapes + script + attente de connexion |
| 7 | Sessions actives | `sessions.html` | Temps réel, consommation, déconnexion |
| 8 | Forfaits | `plans.html` | Offres, prix, quotas, sync routeur |
| 9 | Vouchers | `vouchers.html` | Lots, coupon imprimable, QR, import/export |
| 10 | Caisse | `cashier.html` | Vente en 3 clics, journal, reçu |
| 11 | Équipe & réglages | `settings.html` | Membres, clés API, sécurité, audit |
| 12 | Portail captif | `portal.html` | Achat mobile money + page de confirmation (mobile) |
| 13 | Design system | `design-system.html` | Jetons et composants (référence développeur) |

**Choix technique du prototype** : HTML + CSS + 60 lignes de JS, **aucune dépendance externe**
(pas de CDN, pas de police distante). Raison : le prototype doit s'ouvrir vite, hors ligne, et
rester lisible par un développeur — il ne doit pas devenir une seconde application à maintenir.
La cible d'implémentation reste React + Tailwind + shadcn/ui (voir `05-frontend-react.md`).

---

## 2. Jetons (tokens)

Les jetons vivent dans `design/styles.css` (`:root`). En production, ils deviennent des variables
CSS globales **et** la configuration Tailwind (`theme.extend`).

### Couleurs

| Jeton | Valeur | Usage |
|---|---|---|
| `--brand-700` / `--brand-600` | `#0b6b5a` / `#0e876f` | Actions primaires, liens, en-têtes |
| `--brand-500` / `--brand-400` | `#0fa37f` / `#2bbf9b` | Accents, graphiques, focus |
| `--brand-100` / `--brand-50` | `#d8f3ea` / `#eefaf6` | Fonds doux, survol de ligne, badges |
| `--accent-500` | `#f2a93b` | Mise en avant ponctuelle (jamais pour un état) |
| `--ink-900` | `#0b1220` | Barre latérale, textes forts, code |
| `--ink-500` | `#5b6b82` | Texte secondaire |
| `--ink-200` | `#dde3ec` | Bordures |
| `--ink-50` | `#f6f8fb` | Fond d'application |
| `--ok-600` / `--warn-600` / `--danger-600` / `--info-600` | vert / ambre / rouge / bleu | États et alertes |

**Règle d'accessibilité** : un statut n'est jamais porté par la couleur seule — toujours
`point + libellé` (ou icône + libellé). Vérifié sur les daltonismes deutéranopie/protanopie.

### Typographie

| Rôle | Taille / graisse | Remarque |
|---|---|---|
| Titre de page | 22 px / 700, `-0.4px` | Un seul par écran |
| Titre de carte | 14 px / 650 | Toujours dans un `card-head` |
| Corps | 13,5 px / 400 | Interligne 1,45 |
| Légende | 11,5–12 px / 400 | Couleur `--ink-400` |
| Donnée technique | 12,5 px monospace | Séries, IP, MAC, commandes |
| Chiffres | `font-variant-numeric: tabular-nums` | Obligatoire pour les montants et les colonnes |

Police : **pile système** (aucun téléchargement). C'est un choix de performance assumé pour la 3G.

### Espacement, rayons, ombres

- Échelle : 4 / 8 / 12 / 16 / 22 / 24 px (pas de valeurs arbitraires).
- Rayons : 6 px (petit), 10 px (défaut), 14 px (cartes), 20 px (grandes surfaces).
- Ombres : `sm` (cartes), `md` (survol), `lg` (modale, téléphone du portail). Aucune ombre décorative.

---

## 3. Composants

| Composant | Variantes / états | Règles |
|---|---|---|
| **Bouton** | primaire, secondaire, discret, danger, danger doux ; sm / md / lg ; désactivé ; icône | **Un seul bouton primaire par écran.** Libellé à l'infinitif, jamais « OK » |
| **Badge de statut** | ok, alerte, erreur, info, marque, live ; avec/sans point | Jamais cliquable ; hauteur 22 px fixe |
| **Carte** | en-tête + corps, corps compact | Pas d'imbrication de cartes ; une carte = un sujet |
| **KPI** | valeur + delta + contexte | Le delta porte une flèche **et** un texte ; pas de couleur seule |
| **Tableau** | standard, compact, sélection, pagination par curseur | En-têtes en majuscules 11 px ; chiffres alignés à droite ; ligne survolée en `brand-50` |
| **Champs** | input, select, textarea, groupe avec addon (FCFA, Go, Mbps) | Libellé **au-dessus**, aide en dessous, erreur en rouge sous le champ |
| **Interrupteur** | on / off | Réservé aux réglages à effet immédiat ; sinon case à cocher |
| **Onglets** | standard, avec compteur | Reflètent l'URL (deep-link), pas un état caché |
| **Assistant (stepper)** | à faire / en cours / terminé | Toujours visible pendant le parcours ; retour possible sauf étape validée |
| **Bloc de code** | avec bouton copier, défilement | Jamais de secret complet à l'écran au-delà de l'action d'enrôlement |
| **Bandeau** | info, alerte, erreur, marque | En haut de zone, une action maximum à droite |
| **Modale** | confirmation simple, confirmation à saisie | Actions destructrices = saisie du nom de l'objet |
| **Toast** | succès, erreur | 4 s, empilable, jamais porteur d'une action critique |
| **État vide / squelette** | — | Un état vide propose toujours l'action suivante |

---

## 4. Écrans : points de conception

### Tableau de bord
- Réponse à **une** question : « est-ce que ça marche et est-ce que je gagne de l'argent ? ».
- Ordre : alertes → 4 KPI → recette (14 j) + alertes → parc + encaissements.
- Un seul appel API (`GET /dashboard`) pour tenir la promesse < 300 ms.

### Parc de routeurs
- Colonnes utiles au support : nom + série + IP, site, statut, version, clients, **disque**, dernier contact.
- Filtres persistants dans l'URL (partage de lien entre techniciens).
- Bandeau de sécurité rappelant que le parc est joint par tunnel.

### Fiche routeur
- Action principale : « Synchroniser ». « Redémarrer » est en **danger doux** + confirmation.
- Onglets : Vue d'ensemble, Interfaces, Sessions, Vouchers, Configuration, Événements, Réglages.
- Le graphique affiche débit et la table donne les compteurs : un technicien doit pouvoir diagnostiquer
  sans quitter la page.

### Enrôlement
- Promesse tenue : **coller un script, attendre, c'est prêt**. Trois étapes visibles, une seule action.
- Script en bloc copiable + `.rsc` téléchargeable + QR pour ouvrir sur téléphone.
- Encadré « si ça ne marche pas » avec les 3 causes réelles (collage tronqué, UDP bloqué, horloge).
- Secret à usage unique, valable 24 h, jamais réaffichable.

### Sessions actives
- Badge « live » + heure de dernière actualisation **visible** (confiance).
- Déconnexion unitaire avec confirmation ; « tout déconnecter » réservé à l'admin.
- Colonnes : code, IP, MAC, routeur, débit, volume, durée, paiement.

### Caisse
- **3 clics, 5 secondes** : forfait → moyen de paiement → encaisser. Utilisable au clavier.
- Le ticket apparaît en grand (code + QR), avec impression et WhatsApp.
- Totaux par moyen de paiement affichés en permanence (contrôle de caisse en fin de journée).

### Portail captif
- Deux écrans : achat (offres + mobile money) et confirmation (code, quota, temps restant).
- Boutons opérateurs reconnaissables par la couleur et le nom ; cible tactile ≥ 44 px.
- Aucune inscription, aucun mot de passe : le code suffit.

### Équipe & réglages
- Rôles lisibles en français, jamais des noms techniques.
- Clés API : le secret n'est affiché **qu'une fois**, avec rappel des scopes.
- Journal d'audit immuable, exportable, filtrable.

---

## 5. Responsive et connexions faibles

| Point de rupture | Comportement |
|---|---|
| ≥ 1200 px | Console complète, 4 colonnes de KPI, sidebar fixe |
| 980–1200 px | KPI sur 2 colonnes, graphiques empilés |
| < 980 px | Sidebar en barre horizontale défilante, tableaux en défilement |
| < 620 px | Une colonne, recherche masquée (atteignable par le menu), boutons pleine largeur |

Contraintes de performance (prototype et production) :
- JS initial < 250 Ko gzip, aucune police distante, images < 60 Ko.
- Tout graphique est un SVG inline généré côté serveur pour le prototype ; en production, `uPlot`
  chargé en `import()` différé au-delà de 200 points.
- Les exports (PDF, CSV) sont produits côté serveur, jamais dans le navigateur.

---

## 6. Accessibilité (cible AA)

- Contrastes vérifiés : texte fort sur blanc ≥ 7:1 ; secondaire ≥ 4,5:1 ; badges ≥ 4,5:1.
- Navigation clavier complète, focus visible (`outline` 3 px `brand-500` à 15 % d'opacité).
- Libellés de formulaires associés (`for`/`id`), erreurs annoncées (`aria-live`).
- Cibles tactiles ≥ 44 × 44 px sur le portail (usage pouce, en plein soleil).
- Aucune information portée uniquement par la couleur ; icônes décoratives en `aria-hidden`.

---

## 7. Contenu et langue

- **Français** par défaut, ton direct, pas de jargon inutile : « Hors ligne » et non « NAS unreachable ».
- Les termes techniques restent en monospace quand ils sont copiables (IP, MAC, commandes).
- Montants : `84 500 FCFA`, séparateur insécable, jamais de décimales (XOF).
- Dates : « il y a 12 s », « hier 22:00 », fuseau `Africa/Ouagadougou` ; l'ISO reste en infobulle.
- Erreurs : cause probable + action. Exemple : « Routeur injoignable — le tunnel a repris 3 fois
  cette heure. Vérifier la sortie UDP 51820. »

---

## 8. Du prototype au code

| Prototype | Cible React |
|---|---|
| `styles.css` (`:root`) | `tailwind.config` + variables CSS globales |
| Classes `.btn`, `.badge`, `.card` | Composants `Button`, `Badge`, `Card` (variantes en `cva`) |
| `.table` | TanStack Table + composant `DataTable` (pagination serveur) |
| `.tabs` | Onglets routés (`useSearchParams`) |
| `.stepper` | Composant `Wizard` réutilisé par l'enrôlement et l'import |
| Graphiques SVG | `uPlot` / `Recharts` alimentés par `/usage` |
| `app.js` | Remplacé par TanStack Query + WebSocket (`05-frontend-react.md`) |

**Checklist de remise aux développeurs**
- [ ] Les 13 écrans existent en variantes **vide / chargement / erreur** (le prototype ne montre que la nominale).
- [ ] Chaque action destructrice a sa modale de confirmation.
- [ ] Chaque écran liste l'endpoint qu'il consomme (colonne ajoutée dans le tableau §1 du contrat d'API).
- [ ] Les états temps réel ont un repli en actualisation manuelle.
- [ ] Les libellés sont externalisés (`i18n`), aucune chaîne en dur dans le JSX.
- [ ] Le thème clair est validé ; le thème sombre est optionnel (techniciens).

---

## 9. À tester avec de vrais utilisateurs (avant le code UI)

1. **Caissier** : vendre un voucher sans explication préalable → mesure du temps et des hésitations.
2. **Technicien** : enrôler un routeur à partir de la seule page d'assistance → taux de réussite.
3. **Gérant** : retrouver « combien j'ai encaissé hier » en moins de 15 secondes.
4. **Client final** : acheter un voucher sur un téléphone d'entrée de gamme, en 3G, en plein soleil.
5. **Support** : diagnostiquer un routeur hors ligne sans aide.

Chaque session : 5 personnes, 15 minutes, notes écrites. Les résultats doivent modifier les maquettes
**avant** le développement de l'interface, pas après.
