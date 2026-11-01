import { useState } from 'react';
import Modal from './Modal.jsx';
import { api } from '../lib/api.js';

/**
 * Génération d'un lot de codes pour un site et un forfait.
 *
 * @param {{sites: any[], plans: any[], onClose: Function, onCreated: Function}} props Données et rappels.
 * @returns {JSX.Element} La modale.
 */
export default function GenerateBatchModal({ sites, plans, onClose, onCreated }) {
  const [form, setForm] = useState({
    site_id: sites[0]?.id || '',
    plan_id: plans[0]?.id || '',
    quantity: 20,
    prefix: sites[0]?.code?.replace(/[^A-Z0-9]/gi, '') || '',
    note: '',
  });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const total = (plans.find((plan) => plan.id === form.plan_id)?.price_fcfa || 0) * Number(form.quantity);

  /**
   * Crée le lot puis ferme la modale.
   *
   * @param {React.FormEvent} event Soumission.
   * @returns {Promise<void>}
   */
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.post('/voucher-batches/', {
        ...form,
        quantity: Number(form.quantity),
      });
      await onCreated();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Générer un lot de vouchers" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="grid-2">
          <label className="field">
            <span>Site</span>
            <select
              value={form.site_id}
              onChange={(event) => setForm({ ...form, site_id: event.target.value })}
              required
            >
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name} ({site.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Forfait</span>
            <select
              value={form.plan_id}
              onChange={(event) => setForm({ ...form, plan_id: event.target.value })}
              required
            >
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} · {plan.price_fcfa} FCFA
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid-3">
          <label className="field">
            <span>Quantité (max 500)</span>
            <input
              type="number"
              min="1"
              max="500"
              value={form.quantity}
              onChange={(event) => setForm({ ...form, quantity: event.target.value })}
            />
          </label>
          <label className="field">
            <span>Préfixe</span>
            <input
              value={form.prefix}
              maxLength="6"
              onChange={(event) => setForm({ ...form, prefix: event.target.value.toUpperCase() })}
              placeholder="CC01"
            />
          </label>
          <label className="field">
            <span>Valeur du lot</span>
            <input value={`${total.toLocaleString('fr-FR')} FCFA`} readOnly />
          </label>
        </div>
        <label className="field">
          <span>Note (facultatif)</span>
          <input
            value={form.note}
            onChange={(event) => setForm({ ...form, note: event.target.value })}
            placeholder="Caisse du 12/11"
          />
        </label>

        {error ? <p className="alert alert-danger">{error}</p> : null}

        <div className="row-between">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Annuler
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Génération…' : `Générer ${form.quantity} codes`}
          </button>
        </div>
      </form>
    </Modal>
  );
}
