import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, downloadFile, items } from '../lib/api.js';
import { formatDate } from '../lib/format.js';
import PlanModal from '../components/PlanModal.jsx';
import GenerateBatchModal from '../components/GenerateBatchModal.jsx';

const STATE_FILTERS = [
  { value: '', label: 'Tous' },
  { value: 'unused', label: 'Générés' },
  { value: 'provisioned', label: 'Sur le routeur' },
  { value: 'active', label: 'Utilisés' },
  { value: 'exhausted', label: 'Quota épuisé' },
  { value: 'revoked', label: 'Révoqués' },
];

/**
 * Écran vouchers : forfaits, lots générés, envoi au routeur, export et codes.
 *
 * @returns {JSX.Element} La page.
 */
export default function VouchersPage() {
  const [plans, setPlans] = useState([]);
  const [batches, setBatches] = useState([]);
  const [sites, setSites] = useState([]);
  const [vouchers, setVouchers] = useState([]);
  const [selected, setSelected] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [showPlan, setShowPlan] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const [planData, batchData, siteData] = await Promise.all([
      api.get('/plans/'),
      api.get('/voucher-batches/'),
      api.get('/sites/'),
    ]);
    setPlans(items(planData));
    setBatches(items(batchData));
    setSites(items(siteData));
    return items(batchData);
  }, []);

  const loadVouchers = useCallback(async (batchId, state) => {
    if (!batchId) {
      setVouchers([]);
      return;
    }
    const query = new URLSearchParams({ batch: batchId, page_size: '200' });
    if (state) query.set('state', state);
    setVouchers(items(await api.get(`/vouchers/?${query}`)));
  }, []);

  useEffect(() => {
    reload()
      .catch((failure) => setError(failure.message))
      .finally(() => setLoading(false));
  }, [reload]);

  useEffect(() => {
    if (!selected && batches.length > 0) setSelected(batches[0].id);
  }, [batches, selected]);

  useEffect(() => {
    loadVouchers(selected, stateFilter).catch((failure) => setError(failure.message));
  }, [selected, stateFilter, loadVouchers]);

  const selectedBatch = useMemo(
    () => batches.find((batch) => batch.id === selected) || null,
    [batches, selected],
  );

  /**
   * Lance une action sur un lot (envoi, synchronisation) puis rafraîchit.
   *
   * @param {string} action ``provision`` ou ``sync``.
   * @param {object} batch Lot concerné.
   */
  async function runBatchAction(action, batch) {
    setBusy(`${action}:${batch.id}`);
    setError('');
    setMessage(null);
    try {
      const result = await api.post(`/voucher-batches/${batch.id}/${action}/`);
      const text =
        action === 'provision'
          ? `${result.pushed} code(s) envoyé(s) au routeur${result.failed ? `, ${result.failed} échec(s)` : ''}.`
          : `${result.checked} code(s) lus · ${result.activated} activé(s) · ${result.exhausted} épuisé(s) · ${result.expired} expiré(s).`;
      setMessage({ tone: result.failed ? 'warn' : 'ok', text, errors: result.errors || [] });
      await reload();
      await loadVouchers(selected, stateFilter);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy('');
    }
  }

  /**
   * Télécharge l'export CSV d'un lot.
   *
   * @param {object} batch Lot concerné.
   */
  async function exportBatch(batch) {
    try {
      await downloadFile(`/voucher-batches/${batch.id}/export/`, `vouchers-${batch.site.code}.csv`);
    } catch (failure) {
      setError(failure.message);
    }
  }

  return (
    <section className="stack">
      <header className="page-head">
        <div>
          <h1>Vouchers</h1>
          <p className="muted">
            Codes prépayés : génération, envoi au routeur, suivi des quotas et export caisse.
          </p>
        </div>
        <div className="row">
          <button type="button" className="btn btn-secondary" onClick={() => setShowPlan(true)}>
            Nouveau forfait
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowGenerate(true)}
            disabled={sites.length === 0 || plans.length === 0}
          >
            Générer un lot
          </button>
        </div>
      </header>

      {error ? <p className="alert alert-danger">{error}</p> : null}
      {message ? (
        <div className={`alert alert-${message.tone === 'ok' ? 'ok' : 'warn'}`}>
          {message.text}
          {message.errors?.length ? (
            <ul className="small mt-8">
              {message.errors.slice(0, 3).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <div className="panel">
        <div className="panel-head">
          <h2>Forfaits</h2>
          <span className="muted small">{plans.length} actif(s)</span>
        </div>
        {plans.length === 0 && !loading ? (
          <p className="muted">
            Créez d'abord un forfait (durée, volume, prix) : il détermine la limite appliquée par
            le routeur.
          </p>
        ) : (
          <div className="plans">
            {plans.map((plan) => (
              <div key={plan.id} className="plan-card">
                <div className="row-between">
                  <strong>{plan.name}</strong>
                  <span className="badge badge-pending">{plan.code}</span>
                </div>
                <span className="plan-price">{plan.price_fcfa.toLocaleString('fr-FR')} FCFA</span>
                <span className="muted small">
                  {plan.duration_label} · {plan.data_cap_mb ? `${plan.data_cap_mb} Mo` : 'illimité'}
                  {plan.rate_limit ? ` · ${plan.rate_limit}` : ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Lots générés</h2>
          <span className="muted small">{loading ? 'chargement…' : `${batches.length} lot(s)`}</span>
        </div>
        {batches.length === 0 && !loading ? (
          <div className="empty">
            <p>Aucun lot de codes.</p>
            <p className="muted">Générez 20 codes pour tester avec votre routeur.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Lot</th>
                <th>Site</th>
                <th>Forfait</th>
                <th>Codes</th>
                <th>Actifs</th>
                <th>Routeur</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {batches.map((batch) => (
                <tr
                  key={batch.id}
                  className={batch.id === selected ? 'row-selected' : ''}
                  onClick={() => setSelected(batch.id)}
                >
                  <td>
                    <strong className="mono">{batch.prefix ? `${batch.prefix}-…` : 'sans préfixe'}</strong>
                    <div className="muted small">{formatDate(batch.created_at)}</div>
                  </td>
                  <td>{batch.site.code}</td>
                  <td>
                    {batch.plan.name}
                    <div className="muted small">{batch.plan.duration_label}</div>
                  </td>
                  <td className="mono">{batch.counts.total}</td>
                  <td className="mono">{batch.counts.active}</td>
                  <td>
                    {batch.provisioned_at ? (
                      <span className="badge badge-online">envoyé</span>
                    ) : (
                      <span className="badge badge-pending">à envoyer</span>
                    )}
                  </td>
                  <td className="right nowrap">
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={(event) => {
                        event.stopPropagation();
                        runBatchAction('provision', batch);
                      }}
                      disabled={busy !== ''}
                    >
                      {busy === `provision:${batch.id}` ? 'Envoi…' : 'Envoyer'}
                    </button>{' '}
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={(event) => {
                        event.stopPropagation();
                        runBatchAction('sync', batch);
                      }}
                      disabled={busy !== ''}
                    >
                      Sync
                    </button>{' '}
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={(event) => {
                        event.stopPropagation();
                        exportBatch(batch);
                      }}
                    >
                      CSV
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Codes {selectedBatch ? `· ${selectedBatch.plan.name}` : ''}</h2>
          <div className="row wrap">
            {STATE_FILTERS.map((filter) => (
              <button
                key={filter.value}
                type="button"
                className={`chip ${stateFilter === filter.value ? 'chip-active' : ''}`}
                onClick={() => setStateFilter(filter.value)}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
        {vouchers.length === 0 ? (
          <p className="muted">Aucun code pour ce filtre.</p>
        ) : (
          <table className="table table-compact">
            <thead>
              <tr>
                <th>Code</th>
                <th>Mot de passe</th>
                <th>État</th>
                <th className="right">Consommé</th>
                <th>Activé</th>
                <th>Expire</th>
              </tr>
            </thead>
            <tbody>
              {vouchers.map((voucher) => (
                <tr key={voucher.id}>
                  <td className="mono strong">{voucher.code}</td>
                  <td className="mono">{voucher.password}</td>
                  <td>
                    <span className={`badge badge-${badgeTone(voucher.state)}`}>
                      {voucher.state_label}
                    </span>
                  </td>
                  <td className="right mono">
                    {voucher.used_bytes ? `${Math.round(voucher.used_bytes / 1048576)} Mo` : '—'}
                  </td>
                  <td className="muted small">{formatDate(voucher.activated_at)}</td>
                  <td className="muted small">{formatDate(voucher.expires_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showPlan ? (
        <PlanModal
          onClose={() => setShowPlan(false)}
          onCreated={async () => {
            setShowPlan(false);
            await reload();
          }}
        />
      ) : null}

      {showGenerate ? (
        <GenerateBatchModal
          sites={sites}
          plans={plans}
          onClose={() => setShowGenerate(false)}
          onCreated={async () => {
            setShowGenerate(false);
            const fresh = await reload();
            if (fresh.length > 0) setSelected(fresh[0].id);
          }}
        />
      ) : null}
    </section>
  );
}

/**
 * Associe un état de voucher à une couleur de badge.
 *
 * @param {string} state État renvoyé par l'API.
 * @returns {string} Suffixe de classe CSS.
 */
function badgeTone(state) {
  if (state === 'active') return 'online';
  if (state === 'exhausted') return 'degraded';
  if (state === 'revoked' || state === 'expired') return 'unreachable';
  return 'pending';
}
