import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, items } from '../lib/api.js';
import { since } from '../lib/format.js';
import StatusBadge from '../components/StatusBadge.jsx';

/**
 * Tableau de bord : indicateurs du parc et derniers contacts.
 *
 * @returns {JSX.Element} La page.
 */
export default function DashboardPage() {
  const [devices, setDevices] = useState([]);
  const [sites, setSites] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get('/devices/'), api.get('/sites/')])
      .then(([deviceData, siteData]) => {
        setDevices(items(deviceData));
        setSites(items(siteData));
      })
      .catch((failure) => setError(failure.message))
      .finally(() => setLoading(false));
  }, []);

  const online = devices.filter((device) => device.status === 'online').length;
  const offline = devices.filter((device) => device.status === 'unreachable').length;
  const pending = devices.filter((device) => !device.is_enrolled).length;

  return (
    <section className="stack">
      <header className="page-head">
        <div>
          <h1>Tableau de bord</h1>
          <p className="muted">État du parc et actions rapides.</p>
        </div>
        <Link className="btn btn-primary" to="/devices">
          Gérer les routeurs
        </Link>
      </header>

      {error ? <p className="alert alert-danger">{error}</p> : null}

      <div className="stats">
        <Stat label="Routeurs" value={devices.length} hint={`${sites.length} site(s)`} />
        <Stat label="En ligne" value={online} tone="ok" hint="contact < 5 min conseillé" />
        <Stat label="Hors ligne" value={offline} tone={offline ? 'danger' : 'plain'} hint="dernier statut connu" />
        <Stat label="À enrôler" value={pending} tone={pending ? 'warn' : 'plain'} hint="script non encore appliqué" />
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Derniers routeurs</h2>
          <span className="muted small">{loading ? 'chargement…' : `${devices.length} au total`}</span>
        </div>

        {devices.length === 0 && !loading ? (
          <div className="empty">
            <p>Aucun routeur pour l'instant.</p>
            <p className="muted">
              Ajoutez votre routeur x86 (VirtualBox) puis testez la connexion depuis sa fiche.
            </p>
            <Link className="btn btn-primary" to="/devices">
              Ajouter un routeur
            </Link>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Routeur</th>
                <th>Site</th>
                <th>État</th>
                <th>RouterOS</th>
                <th>Dernier contact</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {devices.slice(0, 8).map((device) => (
                <tr key={device.id}>
                  <td>
                    <Link to={`/devices/${device.id}`}>{device.name}</Link>
                    <div className="muted small mono">{device.management_ip || 'IP à définir'}</div>
                  </td>
                  <td>{device.site?.name || '—'}</td>
                  <td>
                    <StatusBadge status={device.status} />
                  </td>
                  <td className="mono">{device.ros_version || '—'}</td>
                  <td>{since(device.last_seen_at)}</td>
                  <td className="right">
                    <Link className="btn btn-secondary btn-sm" to={`/devices/${device.id}`}>
                      Ouvrir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

/**
 * Carte d'indicateur.
 *
 * @param {{label: string, value: number, hint?: string, tone?: string}} props Libellé, valeur et ton.
 * @returns {JSX.Element} La carte.
 */
function Stat({ label, value, hint, tone = 'plain' }) {
  return (
    <div className={`stat stat-${tone}`}>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {hint ? <span className="muted small">{hint}</span> : null}
    </div>
  );
}
