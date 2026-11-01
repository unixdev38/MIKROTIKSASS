import { useState } from 'react';
import { useAuth } from '../auth/AuthProvider.jsx';

/**
 * Écran de connexion (JWT) : e-mail, mot de passe, message d'erreur explicite.
 *
 * @returns {JSX.Element} Le formulaire de connexion.
 */
export default function LoginPage() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('demo@kora.bf');
  const [password, setPassword] = useState('demo-mot-de-passe-2026');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  /**
   * Soumet le formulaire de connexion.
   *
   * @param {React.FormEvent} event Événement de soumission.
   * @returns {Promise<void>}
   */
  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await signIn(email.trim(), password);
    } catch (failure) {
      setError(failure.message || 'Connexion impossible.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="brand brand-large">
          <span className="brand-mark">K</span>
          <span>
            <strong>Kora</strong>
            <small>console de gestion MikroTik</small>
          </span>
        </div>

        <h1>Connexion</h1>
        <p className="muted">Accédez à votre parc, vos vouchers et votre supervision.</p>

        <label className="field">
          <span>Adresse e-mail</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="field">
          <span>Mot de passe</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error ? <p className="alert alert-danger">{error}</p> : null}

        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Connexion…' : 'Se connecter'}
        </button>

        <p className="hint">
          Compte de démonstration : <code>demo@kora.bf</code> · mot de passe{' '}
          <code>demo-mot-de-passe-2026</code> (créé par <code>make demo</code>).
        </p>
      </form>
    </div>
  );
}
