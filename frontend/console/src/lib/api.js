/**
 * Client HTTP de la console.
 *
 * Responsabilités : conserver la session (jetons + espace actif), appeler l'API,
 * rafraîchir automatiquement le jeton d'accès expiré et traduire les erreurs
 * « problem+json » en messages lisibles.
 */

const STORAGE = { access: 'kora.access', refresh: 'kora.refresh', tenant: 'kora.tenant' };

/** Erreur d'API portant le code métier renvoyé par le serveur. */
export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

/** Mémoire locale de la session (jetons JWT et espace de travail). */
export const session = {
  get access() {
    return localStorage.getItem(STORAGE.access);
  },
  get refresh() {
    return localStorage.getItem(STORAGE.refresh);
  },
  get tenant() {
    return localStorage.getItem(STORAGE.tenant);
  },
  save({ access, refresh, tenant }) {
    if (access) localStorage.setItem(STORAGE.access, access);
    if (refresh) localStorage.setItem(STORAGE.refresh, refresh);
    if (tenant) localStorage.setItem(STORAGE.tenant, tenant);
  },
  setTenant(slug) {
    if (slug) localStorage.setItem(STORAGE.tenant, slug);
  },
  clear() {
    Object.values(STORAGE).forEach((key) => localStorage.removeItem(key));
  },
};

/**
 * Extrait un message lisible d'une réponse d'erreur.
 *
 * @param {any} data Corps décodé (problem+json, erreurs DRF ou vide).
 * @param {number} status Code HTTP.
 * @returns {string} Message destiné à l'utilisateur.
 */
function messageFrom(data, status) {
  if (!data) return `Erreur ${status}`;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  if (data.title) return data.title;
  if (data.errors) {
    const [field, messages] = Object.entries(data.errors)[0] || [];
    const first = Array.isArray(messages) ? messages[0] : messages;
    return field ? `${field} : ${first}` : String(first);
  }
  const [field, messages] = Object.entries(data)[0] || [];
  const first = Array.isArray(messages) ? messages[0] : messages;
  return field ? `${field} : ${first}` : `Erreur ${status}`;
}

/**
 * Envoie une requête brute et décode la réponse.
 *
 * @param {string} path Chemin relatif à `/api/v1` (ex. `/devices/`).
 * @param {object} [options] Options : `method`, `body`, `token`, `tenant`.
 * @returns {Promise<any>} Charge utile décodée.
 * @throws {ApiError} Si le serveur répond une erreur.
 */
async function send(path, { method = 'GET', body, token, tenant, anonymous = false } = {}) {
  const headers = { Accept: 'application/json' };
  if (body) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  if (tenant) headers['X-Tenant-Slug'] = tenant;

  const response = await fetch(`/api/v1${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) {
    throw new ApiError(messageFrom(data, response.status), {
      status: response.status,
      code: data?.code,
    });
  }
  return data;
}

/** Renouvelle le jeton d'accès à partir du refresh token. */
async function refreshAccess() {
  const refresh = session.refresh;
  if (!refresh) throw new ApiError('Session expirée', { status: 401, code: 'no_refresh' });
  const data = await send('/auth/refresh/', { method: 'POST', body: { refresh } });
  session.save({ access: data.access, refresh: data.refresh || refresh });
  return data.access;
}

/**
 * Appelle l'API avec le jeton courant, en le renouvelant une fois si nécessaire.
 *
 * @param {string} path Chemin relatif à `/api/v1`.
 * @param {object} [options] Options : `method`, `body`.
 * @returns {Promise<any>} Charge utile décodée.
 * @throws {ApiError} Si l'appel échoue après renouvellement.
 */
export async function request(path, options = {}) {
  try {
    return await send(path, { ...options, token: session.access, tenant: session.tenant });
  } catch (error) {
    if (error.status !== 401 || !session.refresh) throw error;
    const access = await refreshAccess();
    return send(path, { ...options, token: access, tenant: session.tenant });
  }
}

/** Raccourcis d'appel. */
export const api = {
  /**
   * Connexion par e-mail et mot de passe.
   *
   * @param {{email: string, password: string}} credentials Identifiants.
   * @returns {Promise<object>} Jetons, profil, espace actif et espaces disponibles.
   */
  async login({ email, password }) {
    const data = await send('/auth/token/', { method: 'POST', body: { email, password } });
    session.save({ access: data.access, refresh: data.refresh, tenant: data.tenant?.slug });
    return data;
  },

  /** Déconnexion : révoque le refresh token côté serveur. */
  async logout() {
    try {
      await send('/auth/logout/', {
        method: 'POST',
        body: { refresh: session.refresh },
        token: session.access,
      });
    } finally {
      session.clear();
    }
  },

  get: (path) => request(path),
  post: (path, body = {}) => request(path, { method: 'POST', body }),
  patch: (path, body = {}) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
};

/**
 * Normalise une liste paginée DRF.
 *
 * @param {any} data Réponse de liste (`{count, results}` ou tableau).
 * @returns {any[]} Les éléments de la page courante.
 */
export function items(data) {
  if (!data) return [];
  return Array.isArray(data) ? data : data.results || [];
}
