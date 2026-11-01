# 10 — Checklists, décisions ouvertes et journal de validation

> Statut : **document de travail vivant** · Dernière mise à jour : 2026-11-01
> À cocher au fur et à mesure. Ce fichier est le tableau de bord du projet avant le code.

---

## 1. Checklist « avant la première ligne de code »

### Validation du besoin
- [ ] 10 entretiens réalisés (cybercafés, hôtels, petits FAI, installateurs) avec notes écrites.
- [ ] Les 3 problèmes les plus cités sont identifiés et chiffrés (temps perdu, argent perdu).
- [ ] Au moins 3 personnes acceptent d'être pilotes et de donner un accès routeur.
- [ ] Prix acceptable testé oralement (question directe : « combien par mois ? »).
- [ ] Un concurrent a été testé par un prospect, et ses limites sont connues.

### Décisions produit
- [ ] Vertical retenu : ☐ Hotspot ☐ FAI/PPPoE ☐ Fleet ☐ Unifié.
- [ ] Périmètre MVP gelé et écrit (dans `00-vision-et-produit.md`).
- [ ] Ce qui est explicitement **exclu** du lancement est écrit.
- [ ] Rôles utilisateurs validés avec un vrai caissier et un vrai technicien.

### Validation technique
- [ ] 3 CHR disponibles (7.11, 7.18, 6.49) et accessibles depuis le poste de dev.
- [ ] Connexion REST testée sur CHR 7.x (`/rest/ip/hotspot/user`).
- [ ] Connexion API binaire testée (8729) avec `librouteros`.
- [ ] `listen` testé : réception d'événements et `cancel` propre.
- [ ] WireGuard monté entre un CHR et une machine de test, à travers un NAT.
- [ ] FreeRADIUS + hotspot CHR : `Access-Accept`, `Interim-Update`, `Session-Timeout` validés.
- [ ] **Test critique** : comportement du hotspot quand RADIUS est arrêté (bascule locale ?).
- [ ] Un routeur physique d'entrée de gamme testé (CPU, mémoire, 500 utilisateurs).
- [ ] Mesure du temps d'application d'un lot de 100 utilisateurs sur un hAP lite.
- [ ] Journal de validation §6 rempli.

### Cadre juridique et administratif
- [ ] Statut d'entreprise prêt (facturation, compte bancaire/mobile money professionnel).
- [ ] CGU + politique de confidentialité rédigées.
- [ ] Contrat de sous-traitance type (nous = sous-traitant) rédigé.
- [ ] Point juridique sur les obligations télécom des **clients** FAI (ARPCE) clarifié.
- [ ] Point juridique sur la protection des données (loi locale, CIL) clarifié.
- [ ] Nom de domaine, e-mail professionnel, page de statut réservés.
- [ ] Compte agrégateur de paiement en cours d'ouverture (délai à anticiper : 4–8 semaines).

### Organisation
- [ ] Dépôt Git, conventions de commit, protection de `main`.
- [ ] Environnement de staging opérationnel.
- [ ] Outil de suivi (issues) et rituel hebdomadaire définis.
- [ ] Budget et runway validés (voir `08-roadmap-budget.md`).
- [ ] Critères d'arrêt écrits (« si X alors on arrête/pivote »).

---

## 2. Décisions à prendre (journal)

| # | Sujet | Options | Décision | Date |
|---|---|---|---|---|
| D1 | Vertical de départ | Hotspot / FAI / Fleet / Unifié | ⬜ à décider | |
| D2 | Version RouterOS minimale | 7.11+ / 7.1+ / 6.49 inclus | ⬜ | |
| D3 | Hébergement | VPS EU / VPS régional / hybride | ⬜ | |
| D4 | Agrégateur de paiement | CinetPay / PayDunya / KkiaPay / direct | ⬜ | |
| D5 | Marque blanche au MVP | oui / non | ⬜ | |
| D6 | Application mobile | PWA / React Native / plus tard | ⬜ | |
| D7 | TLS routeur | certificat auto-signé épinglé / CA interne | ⬜ | |
| D8 | Langue | FR seul / FR+EN dès le départ | ⬜ | |
| D9 | Facturation SaaS | mobile money / virement / carte | ⬜ | |
| D10 | Politique SLA affichée | 99,5 % / pas de SLA en bêta | ⬜ | |

Les décisions structurantes sont consignées dans `09-adr/` (format ADR : contexte, décision,
conséquences, alternatives).

---

## 3. Questions ouvertes

1. **Quel est le vrai coût d'un incident chez le client ?** Si une coupure de 30 min coûte 50 000 FCFA
   à un cybercafé, le SLA et la redondance RADIUS sont à revoir à la hausse — et le prix aussi.
2. **Combien de routeurs un client type possède-t-il réellement ?** Détermine la tarification par site
   ou par routeur.
3. **Le client veut-il imprimer, ou envoyer le code par WhatsApp ?** Change la priorité du module PDF.
4. **Qui encaisse l'argent des vouchers en ligne : nous ou le client ?** Si c'est nous, il faut un
   compte de cantonnement et une comptabilité séparée, plus une commission.
5. **Les clients partagent-ils leurs clients finaux entre plusieurs routeurs ?** (itinérance) —
   impacte la conception du compte unique multi-sites.
6. **Faut-il un mode hors-ligne complet pour la caisse ?** (coupures Internet) — coûteux, à valider.
7. **Quel volume de vouchers par mois et par site ?** Dimensionne l'impression et la génération.
8. **Les routeurs clients sont-ils accessibles à l'équipe du client ?** (risque de config manuelle
   hors plateforme → dérive, à détecter).
9. **Faut-il reprendre les données existantes** (Excel, User Manager) automatiquement à l'inscription ?
10. **Quel est le canal de support réellement utilisé ?** (WhatsApp probablement → à intégrer tôt)

---

## 4. Durcissement d'un routeur client (à appliquer systématiquement)

- [ ] Mot de passe admin fort, unique par routeur, et **MFA** sur les comptes `full`.
- [ ] Utilisateur API dédié, non administrateur, restreint par `address=`.
- [ ] `telnet`, `ftp`, `www`, `ssh` désactivés ; `winbox` limité au tunnel.
- [ ] `api-ssl` uniquement, certificat propre, `api` en clair désactivé.
- [ ] Aucun port de management exposé sur Internet (vérifié depuis l'extérieur).
- [ ] `mac-server` et `mac-winbox` restreints à l'interface LAN.
- [ ] Découverte (`/ip neighbor discovery`) sans informations sensibles sur les interfaces WAN.
- [ ] `romon` désactivé si non utilisé.
- [ ] Firmware à jour, `upgrade` vérifié, sauvegarde de la configuration exportée.
- [ ] Politique de mots de passe (`/system/password`) définie.
- [ ] Journalisation distante activée si le client l'accepte.
- [ ] Isolation des clients hotspot (pas d'accès au LAN, pas d'accès au routeur).
- [ ] Heure synchronisée (NTP) — indispensable pour TLS et RADIUS.
- [ ] Configuration sauvegardée dans la plateforme **avant** toute modification ultérieure.

---

## 5. Checklist de mise en production (go-live)

### Technique
- [ ] `DEBUG=False`, `ALLOWED_HOSTS`, secrets injectés, HTTPS forcé.
- [ ] Migrations appliquées, `migrate --check` propre, restauration testée.
- [ ] Tests d'isolation multi-tenant verts ; tests E2E verts.
- [ ] Supervision et alertes actives (erreurs, disque, files, routeurs, RADIUS, certificats).
- [ ] Runbooks rédigés (8 scénarios, cf. `06-securite-exploitation.md` §5.2).
- [ ] Performance vérifiée : dashboard < 300 ms, 50 utilisateurs simultanés en console.
- [ ] Sauvegarde hors site vérifiée (fichier réellement présent et lisible).
- [ ] Plan de rollback écrit et testé.
- [ ] Page de statut publique en ligne.

### Produit
- [ ] Parcours d'inscription testé par une personne extérieure, sans aide.
- [ ] Enrôlement d'un routeur réussi avec la documentation seule.
- [ ] Impression de vouchers testée sur une imprimante réelle.
- [ ] Messages d'erreur en français, compréhensibles par un non-technicien.
- [ ] CGU, confidentialité et sous-traitance acceptées à l'inscription.
- [ ] Données de démonstration supprimables en un clic (pour les démos).

### Commercial et support
- [ ] 3 clients pilotes avec date de démarrage et attentes écrites.
- [ ] Grille tarifaire publiée (au moins une page publique).
- [ ] Procédure de support (canal, horaires, délai de première réponse).
- [ ] Base de connaissances : 10 articles minimum (enrôlement, vouchers, paiement, dépannage).
- [ ] Contrat type envoyé et relu.
- [ ] Facturation de nos propres clients opérationnelle (sinon on travaille gratuitement).

---

## 6. Journal de validation technique (à remplir)

| Date | Routeur / CHR | Version ROS | Test | Résultat | Notes |
|---|---|---|---|---|---|
| | CHR | 7.11 | Login REST | | |
| | CHR | 7.11 | `print` avec `.proplist` (5 000 utilisateurs) | | |
| | CHR | 7.18 | `!empty` sur `remove` | | |
| | CHR | 6.49 | Login API binaire | | |
| | CHR | 7.18 | `listen` hotspot actif | | |
| | CHR | 7.18 | WireGuard derrière NAT | | |
| | CHR | 7.18 | RADIUS arrêté → bascule locale ? | | |
| | hAP ac² | 7.x | 500 utilisateurs : CPU, durée | | |
| | | | | | |

**Règle** : aucun engagement commercial (prix, SLA, fonctionnalité) ne doit être pris avant que les
lignes « RADIUS arrêté » et « routeur derrière NAT » soient validées.

---

## 7. Rituels de projet

| Fréquence | Rituel | Sortie |
|---|---|---|
| Hebdomadaire | Revue d'avancement vs jalons | Décisions consignées, risques mis à jour |
| Hebdomadaire | Revue de code obligatoire sur `apps/mikrotik`, `apps/billing`, `apps/aaa` | Aucune fusion sans relecture |
| Bimensuelle | Test sur routeur réel | Journal §6 mis à jour |
| Mensuelle | Test de restauration de sauvegarde | Procès-verbal daté |
| Mensuelle | Entretien client (même informel) | Verbatims ajoutés au dossier produit |
| Trimestrielle | Revue de sécurité (dépendances, accès, secrets) | Rapport court |
| Après chaque incident | Post-mortem sans blâme | Action corrective + test ajouté |
