# ADR 0003 — Multi-tenant : schéma partagé + `tenant_id` + RLS

- **Statut** : accepté
- **Date** : 2026-11-01

## Contexte

Chaque client (cybercafé, hôtel, petit FAI) est un tenant avec ses sites, routeurs, forfaits, clients
et factures. Trois stratégies classiques : base par tenant, schéma par tenant (`django-tenants`),
schéma partagé avec discriminant.

Les besoins transverses sont fréquents : supervision de la flotte, statistiques globales, facturation
SaaS, support (accès « en tant que » un tenant, tracé). Le nombre de tenants visé à 12 mois est de
l'ordre de 100–200, avec beaucoup de petites structures.

## Décision

**Base unique, schéma unique, `tenant_id` obligatoire sur toutes les tables métier.**

Garde-fous cumulés :
1. `TenantAwareModel` + manager qui lève une exception si le tenant n'est pas défini dans le contexte.
2. Middleware qui déduit le tenant du JWT (jamais d'un paramètre client) et le pose dans un `ContextVar`.
3. **Row Level Security** PostgreSQL sur les tables sensibles, avec `SET LOCAL app.tenant_id`.
4. Tests automatisés d'isolation sur chaque endpoint (liste et détail) : un tenant ne voit jamais
   les données d'un autre ; on renvoie `404`, pas `403`.
5. Les tâches Celery transportent explicitement le `tenant_id` et le valident.

## Conséquences

**Positives**
- Une seule migration, un seul déploiement, une seule sauvegarde.
- Requêtes transverses triviales (support, facturation SaaS, statistiques).
- Coût d'hébergement minimal pour des centaines de petits tenants.
- RLS offre une deuxième barrière indépendante du code applicatif.

**Négatives**
- Risque de fuite si un développeur oublie un filtre → mitigé par le manager strict, RLS et les tests.
- Restauration sélective d'un tenant plus difficile (contournée par un export logique par tenant).
- Les tables très volumineuses (`radacct`, `usage_samples`) contiennent tous les tenants →
  partitionnement/Timescale nécessaire.

**Réversibilité** : possible mais coûteuse ; c'est pourquoi les garde-fous sont posés dès le premier
modèle, pas après.

## Alternatives écartées

| Alternative | Raison du rejet |
|---|---|
| Schéma par tenant | Migrations × N schémas, connexions DB nombreuses, requêtes transverses pénibles |
| Base par tenant | Explosion opérationnelle, sauvegardes et mises à jour ingérables |
| Pas de RLS, code applicatif seul | Une seule erreur suffit ; la défense en profondeur est peu coûteuse ici |
