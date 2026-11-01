/** Helpers d'affichage (aucune logique métier). */

/**
 * Formate une date ISO en français.
 *
 * @param {string|null} iso Date ISO 8601.
 * @param {boolean} [withTime] Inclut l'heure.
 * @returns {string} Date lisible, ou « — ».
 */
export function formatDate(iso, withTime = true) {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  });
}

/**
 * Formate une durée relative (« il y a 3 min »).
 *
 * @param {string|null} iso Date ISO du dernier contact.
 * @returns {string} Texte relatif, ou « jamais ».
 */
export function since(iso) {
  if (!iso) return 'jamais';
  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `il y a ${seconds} s`;
  if (seconds < 3600) return `il y a ${Math.round(seconds / 60)} min`;
  if (seconds < 86400) return `il y a ${Math.round(seconds / 3600)} h`;
  return `il y a ${Math.round(seconds / 86400)} j`;
}

/**
 * Formate une durée d'uptime en jours/heures.
 *
 * @param {number|undefined} seconds Secondes depuis le démarrage.
 * @returns {string} Durée compacte, ou « — ».
 */
export function uptime(seconds) {
  if (!seconds && seconds !== 0) return '—';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return days ? `${days} j ${hours} h` : `${hours} h`;
}

/**
 * Formate un nombre d'octets.
 *
 * @param {number|undefined} bytes Taille en octets.
 * @returns {string} Taille lisible (Mo, Go…).
 */
export function bytes(value) {
  if (!value) return '—';
  const units = ['o', 'Ko', 'Mo', 'Go'];
  let size = value;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index ? 1 : 0)} ${units[index]}`;
}
