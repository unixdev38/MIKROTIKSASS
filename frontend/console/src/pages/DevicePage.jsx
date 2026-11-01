import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api.js';
import { bytes, formatDate, since, uptime } from '../lib/format.js';
import StatusBadge from '../components/StatusBadge.jsx';
import EnrollModal from '../components/EnrollModal.jsx';
import CredentialsModal from '../components/CredentialsModal.jsx';

/**
 * Fiche d'un routeur : état, santé, enrôlement et connexion réelle.
 *
 * @returns {JSX.Element} La page.
 */
export default function DevicePage() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [probe, setProbe] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [enrollment, setEnrollment] = useState(null);
  const [showCredentials, setShowCredentials] = useState(false);

  const reload = useCallback(async () => {
    const data = await api.get(`/devices/${id}/`);
    setDevice(data);
    return data;
  }, [id]);

  useEffect(() => {
    reload().catch((failure) => setError(failure.message));
  }, [reload]);

  /** Lance un test de connexion et rafraîchit la fiche. */
  async function testConnection() {
    setBusy('probe');
    setError('');
    try {
      const result = await api.post(`/devices/${id}/test-connection/`);
      setProbe(result);
      await reload();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy('');
    }
  }

  /**
   * Génère (ou renouvelle) le script d'enrôlement.
   *
   * @param {boolean} force Demande une rotation des secrets existants.
   */
  async function enroll(force = false) {
    setBusy('enroll');
    setError('');
    try {
      const data = await api.post(`/devices/${id}/enroll/`, { force });
      setEnrollment(data);
      await reload();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy('');
    }
  }

  if (!device) {
    return (
      <section className="stack">
        <Link to="/devices" className="link-back">
          ← Routeurs
        </Link>
        {error ? <p className="alert alert-danger">{error}</p> : <p className="muted">Chargement…</p>}
      </section>
    );
  }

  const health = device.health || {};

  return (
    <section className="stack">
      <Link to="/devices" className="link-back">
        ← Routeurs
      </Link>

      <header className="page-head">
        <div>
          <h1>
            {device.name} <StatusBadge status={device.status} />
          </h1>
          <p className="muted">
            {device.site?.name} · {device.management_ip || 'IP à définir'}:{device.management_port} ·{' '}
            {device.use_tls ? 'https' : 'http'} · {device.transport}
            {device.is_simulated ? ' · simulé' : ''}
          </p>
        </div>
        <div className="row">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowCredentials(true)}
            disabled={busy !== ''}
          >
            Connecter le routeur
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={testConnection}
            disabled={busy !== ''}
          >
            {busy === 'probe' ? 'Test…' : 'Tester la connexion'}
          </button>
        </div>
      </header>

      {error ? <p className="alert alert-danger">{error}</p> : null}
      {probe ? (
        <p className={`alert ${probe.is_ok ? 'alert-ok' : 'alert-danger'}`}>
          {probe.is_ok
            ? `Contact établi en ${probe.latency_ms} ms · RouterOS ${probe.system_info?.version || '—'}`
            : `Échec : ${probe.error}`}
        </p>
      ) : null}

      <div className="stats">
        <Metric label="CPU" value={health.cpu_load_percent != null ? `${health.cpu_load_percent} %` : '—'} />
        <Metric label="Mémoire" value={health.memory_used_percent != null ? `${health.memory_used_percent} %` : '—'} />
        <Metric label="Uptime" value={uptime(health.uptime_seconds)} />
        <Metric label="Dernier contact" value={since(device.last_seen_at)} />
      </div>

      <div className="split">
        <div className="panel">
          <div className="panel-head">
            <h2>Identité</h2>
            <span className="muted small">{formatDate(device.created_at, false)}</span>
          </div>
          <dl className="desc">
            <dt>Modèle</dt>
            <dd>{device.model_name || health.model || '—'}</dd>
            <dt>Numéro de série</dt>
            <dd className="mono">{device.serial || health.serial || '—'}</dd>
            <dt>RouterOS</dt>
            <dd className="mono">{device.ros_version || '—'}</dd>
            <dt>Site</dt>
            <dd>{device.site?.name || '—'}</dd>
            <dt>Identifiants</dt>
            <dd>{device.is_enrolled ? 'enregistrés' : 'aucun'}</dd>
            <dt>Enrôlement</dt>
            <dd>
              {device.enrollment_expires_at
                ? `expire le ${formatDate(device.enrollment_expires_at)}`
                : 'aucun script actif'}
            </dd>
          </dl>
          <div className="row wrap mt-8">
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => enroll(device.is_enrolled)}
              disabled={busy !== ''}
            >
              {busy === 'enroll'
                ? 'Génération…'
                : device.is_enrolled
                  ? 'Nouveau script (rotation des secrets)'
                  : "Générer le script d'enrôlement"}
            </button>
            {device.is_enrolled ? (
              <span className="muted small">
                La rotation invalide immédiatement l'ancien script.
              </span>
            ) : null}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>Interfaces</h2>
            <span className="muted small">{(health.interfaces || []).length} élément(s)</span>
          </div>
          {(health.interfaces || []).length === 0 ? (
            <p className="muted">
              Lancez un test de connexion pour remonter les interfaces et leurs compteurs.
            </p>
          ) : (
            <table className="table table-compact">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Type</th>
                  <th>Lien</th>
                  <th className="right">Reçu</th>
                  <th className="right">Émis</th>
                </tr>
              </thead>
              <tbody>
                {health.interfaces.map((iface) => (
                  <tr key={iface.name}>
                    <td className="mono">{iface.name}</td>
                    <td className="muted small">{iface.kind}</td>
                    <td>
                      {iface.is_disabled ? (
                        <span className="badge badge-pending">désactivée</span>
                      ) : iface.is_running ? (
                        <span className="badge badge-online">up</span>
                      ) : (
                        <span className="badge badge-unreachable">down</span>
                      )}
                    </td>
                    <td className="right mono">{bytes(iface.rx_bytes)}</td>
                    <td className="right mono">{bytes(iface.tx_bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {enrollment ? (
        <EnrollModal
          device={device}
          script={enrollment.script}
          expiresAt={enrollment.expires_at}
          isRenewal={enrollment.is_renewal}
          onClose={() => setEnrollment(null)}
        />
      ) : null}

      {showCredentials ? (
        <CredentialsModal
          device={device}
          onClose={() => setShowCredentials(false)}
          onSaved={async () => {
            setShowCredentials(false);
            await reload();
          }}
        />
      ) : null}
    </section>
  );
}

/**
 * Carte de mesure compacte.
 *
 * @param {{label: string, value: string}} props Libellé et valeur formatée.
 * @returns {JSX.Element} La carte.
 */
function Metric({ label, value }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
    </div>
  );
}
