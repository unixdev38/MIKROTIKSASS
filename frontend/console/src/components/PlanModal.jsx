import { useState } from 'react';
import Modal from './Modal.jsx';
import { api } from '../lib/api.js';

/**
 * Création d'un forfait (durée, volume, prix).
 *
 * @param {{onClose: Function, onCreated: Function}} props Rappels de fermeture et de rafraîchissement.
 * @returns {JSX.Element} La modale.
 */
export default function PlanModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: '',
    code: '',
    duration_minutes: 60,
    price_fcfa: 200,
    data_cap_mb: 0,
    rate_limit: '2M/2M',
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  /**
   * Enregistre le forfait.
   *
   * @param {React.FormEvent} event Soumission.
   * @returns {Promise<void>}
   */
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.post('/plans/', {
        ...form,
        duration_minutes: Number(form.duration_minutes),
        price_fcfa: Number(form.price_fcfa),
        data_cap_mb: Number(form.data_cap_mb),
      });
      await onCreated();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Nouveau forfait" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="grid-2">
          <label className="field">
            <span>Nom</span>
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="1 heure"
              required
            />
          </label>
          <label className="field">
            <span>Code</span>
            <input
              value={form.code}
              onChange={(event) => setForm({ ...form, code: event.target.value.toUpperCase() })}
              placeholder="H1"
              required
            />
          </label>
        </div>
        <div className="grid-3">
          <label className="field">
            <span>Durée (minutes)</span>
            <input
              type="number"
              min="1"
              value={form.duration_minutes}
              onChange={(event) => setForm({ ...form, duration_minutes: event.target.value })}
            />
          </label>
          <label className="field">
            <span>Volume (Mo, 0 = illimité)</span>
            <input
              type="number"
              min="0"
              value={form.data_cap_mb}
              onChange={(event) => setForm({ ...form, data_cap_mb: event.target.value })}
            />
          </label>
          <label className="field">
            <span>Prix (FCFA)</span>
            <input
              type="number"
              min="0"
              value={form.price_fcfa}
              onChange={(event) => setForm({ ...form, price_fcfa: event.target.value })}
            />
          </label>
        </div>
        <label className="field">
          <span>Limite de débit (vide = aucune)</span>
          <input
            value={form.rate_limit}
            onChange={(event) => setForm({ ...form, rate_limit: event.target.value })}
            placeholder="2M/2M"
          />
        </label>

        {error ? <p className="alert alert-danger">{error}</p> : null}

        <div className="row-between">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Annuler
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Création…' : 'Créer le forfait'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
