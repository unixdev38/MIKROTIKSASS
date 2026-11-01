# ADR 0006 — Console en SPA React (Vite) et non en rendu serveur

- **Statut** : accepté
- **Date** : 2026-11-01

## Contexte

Deux familles d'options pour la console : SPA (React + Vite, API séparée) ou rendu serveur
(Next.js, Django templates + HTMX). Le public est majoritairement sur ordinateur au bureau, parfois
sur tablette, en connexion variable. L'équipe connaît React. La console est une application
« outil » : beaucoup de tableaux, d'états et de mises à jour temps réel.

## Décision

**SPA React 19 + TypeScript + Vite**, servie statiquement, consommant l'API REST versionnée.
Bibliothèques : React Router (data router), TanStack Query, Zustand (UI uniquement),
Tailwind + shadcn/ui, Zod. Aucune logique métier critique côté client.

Le **portail captif** est traité différemment : pages légères rendues côté serveur (Django templates
+ HTMX ou HTML statique + appels API), pour rester rapides et accessibles même avec JavaScript
restreint (certains portails MikroTik et navigateurs de téléphones bas de gamme).

## Conséquences

**Positives**
- Séparation nette front/back : l'API est utilisable par des intégrateurs et une future app mobile.
- Expérience fluide (pas de rechargement), cache client maîtrisé, temps réel simple.
- Build statique déployable sur CDN, coût d'hébergement négligeable.
- Recrutement plus facile (React) et écosystème de composants riche.

**Négatives**
- Deux projets à versionner et à déployer (console + API) → monorepo pnpm et contrat OpenAPI généré
  pour éviter la dérive.
- Poids initial du JS : maîtrisé par un budget de 250 Ko gzip et du découpage par route.
- SEO sans objet (application privée) : le portail, lui, est rendu côté serveur.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| Next.js (SSR) | Complexité serveur supplémentaire sans bénéfice : pas de SEO, données authentifiées |
| Django templates + HTMX | Excellent pour le portail, pénible pour des tableaux/états temps réel riches de la console |
| Vue/Angular | Aucune raison décisive ; l'équipe maîtrise React |
| Application mobile native d'abord | Coût et délais trop élevés ; PWA d'abord, React Native ensuite si besoin |
