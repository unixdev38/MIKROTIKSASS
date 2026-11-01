# ADR 0002 — Double backend MikroTik : REST (préféré) + API binaire

- **Statut** : accepté
- **Date** : 2026-11-01

## Contexte

RouterOS propose l'API binaire (8728/8729, depuis toujours) et l'API REST (443, depuis 7.1).
Les deux exposent les mêmes menus. L'API binaire est la seule à offrir `listen` (temps réel) ;
le REST est plus simple à opérer (TLS standard, proxy, outils HTTP) et ne demande pas de dépendance
binaire. Une partie du parc installé est encore en RouterOS 6.49.

## Décision

Une interface `MikroTikGateway` avec deux implémentations :

1. **`RestBackend`** (httpx) — par défaut pour tout le CRUD sur RouterOS ≥ 7.1 ;
2. **`BinaryBackend`** (librouteros) — pour `listen`, pour RouterOS 6, et en repli si le REST échoue.

Un **`FakeBackend`** alimenté par des fixtures permet de tester sans matériel.

Sélection par routeur (`Device.transport`), avec bascule automatique documentée et journalisée.

## Conséquences

**Positives**
- Pas d'enfermement sur une bibliothèque ni sur une version.
- Le mode « pull » (routeur sans tunnel) peut n'utiliser que le REST.
- Les tests unitaires ne dépendent d'aucun routeur.

**Négatives**
- Deux chemins de code à maintenir : les tests contractuels doivent couvrir les deux et produire
  des résultats **identiques** après normalisation.
- Le REST nécessite `www-ssl` + certificat : contrainte de configuration supplémentaire chez le client.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| API binaire seule | Dépendance binaire, TLS moins standard, plus difficile à opérer à travers un proxy |
| REST seule | Pas de `listen` → pas de temps réel correct, et RouterOS 6 exclu |
| `RouterOS-api` (LaiArturs) seule | Orientée v6, moins bonne prise en charge du streaming |
| Client protocole écrit maison | ~800 lignes à maintenir, gain faible au démarrage |
