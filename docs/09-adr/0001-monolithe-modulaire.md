# ADR 0001 — Monolithe modulaire Django plutôt que microservices

- **Statut** : accepté
- **Date** : 2026-11-01
- **Décideurs** : équipe fondatrice

## Contexte

Le produit couvre plusieurs domaines (parc réseau, AAA, facturation, portail, supervision).
L'équipe est petite (2 développeurs au départ) et le temps de mise sur le marché est court.
Une architecture microservices serait « moderne » mais multiplierait les points de défaillance,
les déploiements et la charge d'exploitation.

## Décision

Une seule application Django, découpée en **applications internes** avec des frontières explicites
(`apps/*`), plus des **processus** séparés (web, workers Celery, connecteur MikroTik).
La séparation se fait par processus et par file de tâches, pas par service réseau.

## Conséquences

**Positives**
- Un seul déploiement, une seule base, une seule migration.
- Transactions locales entre billing et provisioning.
- Débogage simple : une trace d'erreur suffit.
- Coût d'infrastructure minimal.

**Négatives**
- Couplage possible si les frontières ne sont pas respectées → discipline de revue + règles de
  dépendance (`api → apps → core`, jamais l'inverse), vérifiées en CI.
- Un seul langage de déploiement ; pas de scaling indépendant d'un domaine.

**Réversibilité** : moyenne. Le jour où un domaine doit être extrait (probablement la collecte de
métriques ou l'AAA), ses frontières existent déjà — extraction sans réécriture.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| Microservices dès le départ | Coût d'exploitation et de coordination hors de portée d'une petite équipe |
| Serverless (Lambda) | Connexions TCP persistantes vers les routeurs et workers longs incompatibles |
| Django + services Go pour le connecteur | Deux stacks à maintenir pour un gain incertain au démarrage |
