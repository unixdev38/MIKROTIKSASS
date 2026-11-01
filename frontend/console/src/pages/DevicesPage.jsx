import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, items } from '../lib/api.js';
import { since } from '../lib/format.js';
import StatusBadge from '../components/StatusBadge.jsx';
import Modal from '../components/Modal.jsx';

const EMPTY_DEVICE = {
  name: '',
  serial: '',
  management_ip: '',
  management_port: 443,
  use_tls: true,
  is_simulated: false,
};

/**
 * Liste des routeurs et formulaire d'ajout (site + routeur).
 *
 * @returns {JSX.Element} La page.
 */
export default function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [sites, setSites] = useState([]);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    const [deviceData, siteData] = await Promise.all([api.get('/devices/'), api.get('/sites/')]);
    setDevices(items(deviceData));
    setSites(items(siteData));
  }, []);

  useEffect(() => {
    reload()
      .catch((failure) => setError(failure.message))
      .finally(() => setLoading(false));
  }, [reload]);

  return (
    <section className="stack">
      <header className="page-head">
        <div>
          <h1>Routeurs</h1>
          <p className="muted">
            {loading ? 'Chargement…' : `${devices.length} routeur(s) sur ${sites.length} site(s)`}
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
          Ajouter un routeur
        </button>
      </header>

      {error ? <p className="alert alert-danger">{error}</p> : null}

      <div className="panel">
        {devices.length === 0 && !loading ? (
          <div className="empty">
            <p>Aucun routeur enregistré.</p>
            <p className="muted">
              Commencez par créer un site, puis déclarez votre routeur (x86 VirtualBox, hAP, CHR).
            </p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Routeur</th>
                <th>Site</th>
                <th>Adresse</th>
                <th>État</th>
                <th>Enrôlé</th>
                <th>Dernier contact</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {devices.map((device) => (
                <tr key={device.id}>
                  <td>
                    <Link to={`/devices/${device.id}`}>{device.name}</Link>
                    <div className="muted small">{device.model_name || 'modèle inconnu'}</div>
                  </td>
                  <td>{device.site?.name || '—'}</td>
                  <td className="mono">
                    {device.management_ip || '—'}:{device.management_port}
                    <span className="muted small"> {device.use_tls ? 'https' : 'http'}</span>
                  </td>
                  <td>
                    <StatusBadge status={device.status} />
                  </td>
                  <td>{device.is_enrolled ? 'oui' : 'non'}</td>
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

      {showCreate ? (
        <CreateDeviceModal
          sites={sites}
          onClose={() => setShowCreate(false)}
          onCreated={async () => {
            setShowCreate(false);
            await reload();
          }}
        />
      ) : null}
    </section>
  );
}

/**
 * Formulaire de création d'un site et d'un routeur.
 *
 * @param {{sites: any[], onClose: Function, onCreated: Function}} props Sites existants et rappels.
 * @returns {JSX.Element} La modale.
 */
function CreateDeviceModal({ sites, onClose, onCreated }) {
  const [siteId, setSiteId] = useState(sites[0]?.id || '');
  const [site, setSite] = useState({ name: '', code: '', city: '' });
  const [device, setDevice] = useState(EMPTY_DEVICE);
  const [newSite, setNewSite] = useState(sites.length === 0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  /**
   * Enregistre le site puis le routeur.
   *
   * @param {React.FormEvent} event Soumission du formulaire.
   * @returns {Promise<void>}
   */
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      let targetSiteId = siteId;
      if (newSite) {
        const created = await api.post('/sites/', {
          name: site.name,
          code: site.code,
          city: site.city,
        });
        targetSiteId = created.id;
      }
      await api.post('/devices/', {
        ...device,
        site_id: targetSiteId,
        management_ip: device.management_ip || null,
        serial: device.serial || '',
      });
      await onCreated();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Ajouter un routeur" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <fieldset className="fieldset">
          <legend>Site</legend>
          {sites.length > 0 ? (
            <label className="field">
              <span>Rattacher à</span>
              <select
                value={newSite ? 'new' : siteId}
                onChange={(event) => {
                  const value = event.target.value;
                  setNewSite(value === 'new');
                  setSiteId(value === 'new' ? '' : value);
                }}
              >
                {sites.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.code})
                  </option>
                ))}
                <option value="new">+ Nouveau site…</option>
              </select>
            </label>
          ) : null}

          {newSite ? (
            <div className="grid-3">
              <label className="field">
                <span>Nom du site</span>
                <input
                  value={site.name}
                  onChange={(event) => setSite({ ...site, name: event.target.value })}
                  placeholder="Cyber Centre-ville"
                  required
                />
              </label>
              <label className="field">
                <span>Code</span>
                <input
                  value={site.code}
                  onChange={(event) => setSite({ ...site, code: event.target.value })}
                  placeholder="CC-01"
                  required
                />
              </label>
              <label className="field">
                <span>Ville</span>
                <input
                  value={site.city}
                  onChange={(event) => setSite({ ...site, city: event.target.value })}
                  placeholder="Ouagadougou"
                />
              </label>
            </div>
          ) : null}
        </fieldset>

        <fieldset className="fieldset">
          <legend>Routeur</legend>
          <label className="field">
            <span>Nom</span>
            <input
              value={device.name}
              onChange={(event) => setDevice({ ...device, name: event.target.value })}
              placeholder="CHR x86 · virtualbox"
              required
            />
          </label>
          <div className="grid-2">
            <label className="field">
              <span>Adresse IP</span>
              <input
                value={device.management_ip}
                onChange={(event) => setDevice({ ...device, management_ip: event.target.value })}
                placeholder="192.168.56.101"
              />
            </label>
            <label className="field">
              <span>Port</span>
              <input
                type="number"
                min="1"
                max="65535"
                value={device.management_port}
                onChange={(event) =>
                  setDevice({ ...device, management_port: Number(event.target.value) })
                }
              />
            </label>
          </div>
          <div className="row wrap">
            <label className="check">
              <input
                type="checkbox"
                checked={device.use_tls}
                onChange={(event) => setDevice({ ...device, use_tls: event.target.checked })}
              />
              <span>HTTPS (service www-ssl)</span>
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={device.is_simulated}
                onChange={(event) => setDevice({ ...device, is_simulated: event.target.checked })}
              />
              <span>Routeur simulé (démonstration)</span>
            </label>
          </div>
        </fieldset>

        {error ? <p className="alert alert-danger">{error}</p> : null}

        <div className="row-between">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Annuler
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
