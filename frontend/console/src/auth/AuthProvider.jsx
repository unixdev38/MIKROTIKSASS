/**
 * Contexte d'authentification : session, profil et espace de travail actif.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, session } from '../lib/api.js';

const AuthContext = createContext(null);

/**
 * Fournit l'état de session à toute l'application.
 *
 * @param {{children: React.ReactNode}} props Enfants React.
 * @returns {JSX.Element} Le fournisseur de contexte.
 */
export function AuthProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', me: null, error: null });

  const loadProfile = useCallback(async () => {
    const me = await api.get('/me/');
    setState({ status: 'ready', me, error: null });
    return me;
  }, []);

  useEffect(() => {
    if (!session.access) {
      setState({ status: 'anonymous', me: null, error: null });
      return;
    }
    loadProfile().catch(() => {
      session.clear();
      setState({ status: 'anonymous', me: null, error: null });
    });
  }, [loadProfile]);

  /**
   * Connecte l'utilisateur et charge son profil.
   *
   * @param {string} email Adresse e-mail.
   * @param {string} password Mot de passe.
   * @returns {Promise<object>} La réponse de connexion (jetons, espace, rôles).
   */
  const signIn = useCallback(
    async (email, password) => {
      const data = await api.login({ email, password });
      session.setTenant(data.tenant?.slug);
      const me = await loadProfile();
      return { data, me };
    },
    [loadProfile],
  );

  /** Déconnecte l'utilisateur et révoque la session. */
  const signOut = useCallback(async () => {
    await api.logout().catch(() => {});
    setState({ status: 'anonymous', me: null, error: null });
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      user: state.me,
      tenant: state.me?.tenant || null,
      role: state.me?.role || null,
      isReady: state.status === 'ready',
      signIn,
      signOut,
      reload: loadProfile,
    }),
    [state, signIn, signOut, loadProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Accède au contexte d'authentification.
 *
 * @returns {object} Session courante et actions de connexion.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth doit être utilisé dans <AuthProvider>.');
  return context;
}
