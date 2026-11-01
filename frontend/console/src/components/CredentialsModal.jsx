import { useState } from 'react';
import Modal from './Modal.jsx';
import { api } from '../lib/api.js';

/**
 * Renseigne les identifiants réels d'un routeur déjà installé (x86 VirtualBox, CHR, hAP).
 *
 * @param {{device: object, onClose: Function, onSaved: Function}} props Routeur et rappels.
 * @returns {JSX.Element} La modale.
 */
export default function CredentialsModal({ device, onClose, onSaved }) {
  const [form, setForm] = useState({
    username: 'admin',
    password: '',
    port: device.management_port || 443,
    use_tls: device.use_tls !== false,
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  /**
   * Enregistre les identifiants côté serveur (chiffrés) puis lance une sonde.
   *
   * @param {React.FormEvent} event Soumission.
   * @returns {Promise<void>}
   */
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.post(`/devices/${device.id}/credentials/`, {
        username: form.username,
        password: form.password,
        port: Number(form.port),
        use_tls: form.use_tls,
        transport: 'rest',
      });
      await api.post(`/devices/${device.id}/test-connection/`);
      await onSaved();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Connecter le routeur réel" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <p className="muted">
          Sur le routeur, activez le service et créez un utilisateur dédié :
        </p>
        <pre className="script script-inline">
{`/ip service enable www-ssl
/ip service set www-ssl port=443
/user group add name=kora policy=read,write,api,rest-api,test
/user add name=kora group=kora password=<mot-de-passe>`}
        </pre>

        <div className="grid-3">
          <label className="field">
            <span>Utilisateur</span>
            <input
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              required
            />
          </label>
          <label className="field">
            <span>Mot de passe</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
            />
          </label>
          <label className="field">
            <span>Port</span>
            <input
              type="number"
              min="1"
              max="65535"
              value={form.port}
              onChange={(event) => setForm({ ...form, port: event.target.value })}
            />
          </label>
        </div>

        <label className="check">
          <input
            type="checkbox"
            checked={form.use_tls}
            onChange={(event) => setForm({ ...form, use_tls: event.target.checked })}
          />
          <span>HTTPS (décochez si seul <code>www</code> est actif)</span>
        </label>

        {error ? <p className="alert alert-danger">{error}</p> : null}

        <div className="row-between">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Annuler
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Connexion…' : 'Enregistrer et tester'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
