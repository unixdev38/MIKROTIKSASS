/** Badge d'état d'un routeur, aligné sur le design system. */
const LABELS = {
  online: 'En ligne',
  degraded: 'Dégradé',
  unreachable: 'Hors ligne',
  pending: 'À enrôler',
  disabled: 'Désactivé',
};

/**
 * Affiche l'état de supervision d'un routeur.
 *
 * @param {{status: string}} props Statut renvoyé par l'API.
 * @returns {JSX.Element} Le badge coloré.
 */
export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status || 'pending'}`}>{LABELS[status] || status}</span>;
}
