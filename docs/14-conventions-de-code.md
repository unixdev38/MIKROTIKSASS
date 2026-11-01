# 14 — Conventions de code (contrat de l'équipe)

> Statut : **normatif** — tout code qui ne respecte pas ce document est refusé en revue.
> S'applique au backend Django et au frontend React.

---

## 1. La règle d'or

> **Une vue ne décide rien. Elle reçoit, elle délègue, elle répond.**

Toute décision métier (calcul, autorisation fine, appel réseau, transaction) vit dans un **service**.
Si on hésite sur « où mettre ce code ? », la réponse est toujours : **pas dans la vue**.

---

## 2. Les couches (et qui a le droit d'appeler qui)

```
            ┌──────────────────────────────────────────────┐
  HTTP  →   │ views.py        (API fine, aucune logique)   │
            └───────────────┬──────────────────────────────┘
                            │ validation de forme uniquement
            ┌───────────────▼──────────────────────────────┐
            │ serializers.py  (types, champs, contraintes) │
            └───────────────┬──────────────────────────────┘
                            │
            ┌───────────────▼──────────────────────────────┐
            │ services.py     (décisions + transactions)   │
            └───────┬───────────────────────┬──────────────┘
                    │                       │
        ┌───────────▼─────────┐   ┌─────────▼──────────────┐
        │ selectors.py (LECT.)│   │ gateway / clients (I/O)│
        └───────────┬─────────┘   └─────────┬──────────────┘
                    │                       │
            ┌───────▼───────────────────────▼──────────────┐
            │ models.py  (structure + invariants simples)   │
            └──────────────────────────────────────────────┘

  tasks.py (Celery) : appelle un service, jamais l'ORM directement.
```

| Couche | Contenu autorisé | Interdit |
|---|---|---|
| `views.py` | résolution du tenant, appel de service, sérialisation de sortie, codes HTTP | `Model.objects…`, calculs, `if` métier, appels réseau |
| `serializers.py` | validation de **forme** (types, longueurs, formats) | règles métier, accès base pour décider, écritures |
| `services.py` | règles métier, transactions, orchestration, idempotence | HTTP, `request`, formatage d'affichage |
| `selectors.py` | lectures complexes, filtres, `select_related`, agrégats | écritures |
| `models.py` | champs, contraintes, `__str__`, petites propriétés | appels externes, effets de bord |
| `tasks.py` | point d'entrée asynchrone, retry, journalisation | logique métier dupliquée |
| `gateway.py` / `backends/` | protocole externe (HTTP, socket), normalisation | accès base de données |
| `scripts.py` | génération de texte (scripts RouterOS, gabarits) | décisions, accès base |

**Sens des dépendances** : `api → services → selectors/models`. Un service ne connaît jamais une vue.
Le paquet `mikrotik` ne connaît ni la facturation ni le portail.

---

## 3. Tailles maximales (vérifiées en revue)

| Élément | Limite dure | Cible |
|---|---|---|
| Fonction / méthode | **300 lignes** | 30 lignes |
| Fichier | **300 lignes** | 150 lignes |
| Classe | 300 lignes | 120 lignes |
| Paramètres d'une fonction | 5 (au-delà : objet de commande) | 3 |
| Profondeur d'imbrication | 3 | 2 |

Si une fonction dépasse 40 lignes, on extrait : `_etape_1()`, `_etape_2()` ou un objet de commande.
**Une seule responsabilité par fonction, nommée par ce qu'elle fait.**

---

## 4. Héritage : les bases à réutiliser (ne pas réinventer)

| Base | Rôle | Où |
|---|---|---|
| `core.models.TimeStampedModel` | `id` UUID, `created_at`, `updated_at` | tout modèle |
| `core.models.TenantScopedModel` | + `tenant` + manager filtrant par contexte | toute donnée d'un tenant |
| `core.services.BaseService` | unité de travail : `execute()`, acteur, erreurs | tout service |
| `core.api.views.BaseModelViewSet` | vue fine, pagination, erreurs normalisées | toute vue API |
| `core.api.permissions.BaseTenantPermission` | vérifie l'appartenance au tenant | toute vue API |
| `mikrotik.backends.base.BaseBackend` | contrat du connecteur RouterOS | tout backend |
| `core.exceptions.DomainError` | erreur métier traduite en problem+json | tout refus métier |

Règles : **hériter plutôt que copier** ; une base doit rester générique (aucun vocabulaire métier) ;
si on surcharge une méthode, on appelle `super()`.

---

## 5. Docstrings et typage (obligatoires)

- **Toutes** les fonctions, méthodes, classes publiques ont une docstring.
- style **Google** : résumé à l'infinitif, puis `Args`, `Returns`, `Raises`, `Example` si utile.
- **Type hints partout** (paramètres + retour), `from __future__ import annotations` en tête de fichier.
- Les structures de données échangées entre couches sont des `dataclass` typées (pas de `dict` flou).

```python
def issue_enrollment(self, device: Device) -> EnrollmentBundle:
    """Génère un script d'enrôlement à usage unique pour un routeur.

    Crée (ou renouvelle) les identifiants de management du routeur : mot de passe
    de l'utilisateur API, paire de clés WireGuard et jeton de heartbeat. Les secrets
    sont chiffrés avant persistance ; seul le script renvoyé les contient en clair.

    Args:
        device: Routeur cible, rattaché au tenant courant.

    Returns:
        Un ``EnrollmentBundle`` contenant le script prêt à coller dans WinBox,
        l'adresse de management et la date d'expiration du secret.

    Raises:
        DomainError: Si le routeur est déjà enrôlé et que la rotation n'est pas forcée.

    Example:
        >>> bundle = DeviceService(actor=user).issue_enrollment(device)
        >>> print(bundle.script.splitlines()[0])
        # MIKROTIK SAAS — script d'enrôlement v1
    """
```

**Ce qu'une docstring doit rendre inutile** : ouvrir le corps de la fonction. Si un lecteur doit lire
le code pour comprendre les paramètres, la docstring est incomplète.

---

## 6. Nommage

| Élément | Convention | Exemple |
|---|---|---|
| Fichiers | `snake_case` | `device_service.py` |
| Classes | `PascalCase`, suffixe par rôle | `DeviceService`, `EnrollmentBundle`, `RestBackend` |
| Fonctions | verbe + objet | `issue_enrollment`, `probe_device` |
| Booléens | `is_`, `has_`, `can_` | `is_enrolled`, `can_reboot` |
| Constantes | `UPPER_SNAKE` dans `constants.py` | `MAX_VOUCHERS_PER_BATCH` |
| URLs | pluriel, kebab-case | `/api/v1/devices/`, `/voucher-batches/` |
| Champs API | `snake_case` | `last_seen_at` |

Préfixes privés : `_` pour les helpers internes d'un module ou d'une classe.

---

## 7. Erreurs, transactions, idempotence

- Toute erreur métier lève une sous-classe de `DomainError` (`NotFoundError`, `ConflictError`,
  `PermissionDeniedError`, `ExternalServiceError`).
- **Aucune** `Http404`/`ValidationError` DRF levée depuis un service.
- Le handler global traduit en `application/problem+json` (RFC 9457) avec `type`, `title`, `status`,
  `detail`, `request_id`.
- Une écriture multi-tables se fait dans `transaction.atomic()` **dans le service**, jamais dans la vue.
- Toute opération non idempotente reçoit une clé (`Idempotency-Key`) ou un marqueur naturel
  (`comment=saas:<uuid>`) et vérifie l'existence avant de créer.
- Les appels réseau ne sont **jamais** dans une transaction longue.

---

## 8. Configuration

- **Un seul endroit** : `config/settings.py`, alimenté par variables d'environnement
  (`.env` en local, secrets injectés en production).
- Interdits : constantes métier éparpillées dans les vues, `settings.X` dans un template,
  valeur par défaut cachée dans un service.
- Les réglages qui varient par tenant vivent **en base** (`Tenant.settings`), pas dans le code.
- Pas de « configuration dans la vue » : une vue ne lit jamais `settings` pour décider.

---

## 9. Tests

| Type | Portée | Obligatoire |
|---|---|---|
| Unitaire | service, backend, fonction pure | oui |
| Intégration | vue + base + service | oui (1 par endpoint) |
| Isolation | tenant A ≠ tenant B | oui, sur chaque ressource |
| Idempotence | rejouer = même état | oui sur provisioning et paiements |

- `pytest` + `pytest-django`, factories dans `tests/factories.py`.
- Nommage : `test_<comportement>_<condition>_<attendu>`.
- Un test ne dépend pas de l'ordre d'exécution, ni d'un routeur réel (utiliser `FakeBackend`).
- Pas de `time.sleep` ; pas de dépendance réseau dans la suite unitaire.

---

## 10. Ajouter une fonctionnalité : les 6 fichiers, dans cet ordre

1. `models.py` — la donnée et ses contraintes (migration incluse).
2. `selectors.py` — comment on la lit (requêtes + `select_related`).
3. `services.py` — ce qu'on a le droit de faire et dans quel ordre (transaction, audit).
4. `serializers.py` — la forme exposée (entrée/sortie).
5. `views.py` — 10 à 20 lignes : résolution, appel, réponse.
6. `tasks.py` — si c'est lent ou externe : un worker qui appelle le service.

Puis : tests, docstring, mise à jour de `docs/`.

---

## 11. Checklist de revue (à cocher avant chaque fusion)

- [ ] Aucune requête ORM dans une vue ; aucune logique métier dans un serializer.
- [ ] Fonctions < 300 lignes (cible 40) ; fichiers < 300 lignes.
- [ ] Docstrings complètes avec `Args`/`Returns`/`Raises` ; types partout.
- [ ] Les bases (`BaseService`, `TenantScopedModel`, `BaseBackend`) sont réutilisées, pas recopiées.
- [ ] Erreurs métier via `DomainError`, messages en français, aucune fuite de secret dans les logs.
- [ ] `transaction.atomic()` présent sur toute écriture multiple.
- [ ] Test d'isolation multi-tenant ajouté si la ressource est scopée.
- [ ] Test d'idempotence ajouté si l'action peut être rejouée.
- [ ] Configuration ajoutée uniquement dans `settings.py` / `Tenant.settings`.
- [ ] Aucune nouvelle dépendance sans justification écrite dans l'ADR ou la PR.
