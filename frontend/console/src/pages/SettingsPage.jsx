import { useAuth } from '../auth/AuthProvider.jsx';

/**
 * Réglages de session et aide à la connexion d'un routeur local (VirtualBox).
 *
 * @returns {JSX.Element} La page.
 */
export default function SettingsPage() {
  const { user, tenant, role, me, signOut } = useAuth();
  const tenants = me?.tenants || [];

  return (
    <section className="stack">
      <header className="page-head">
        <div>
          <h1>Réglages</h1>
          <p className="muted">Session, espace de travail et connexion d'un routeur de test.</p>
        </div>
      </header>

      <div className="split">
        <div className="panel">
          <div className="panel-head">
            <h2>Session</h2>
            <span className="badge badge-online">JWT</span>
          </div>
          <dl className="desc">
            <dt>Utilisateur</dt>
            <dd>{user?.full_name}</dd>
            <dt>E-mail</dt>
            <dd className="mono">{user?.email}</dd>
            <dt>Espace actif</dt>
            <dd>{tenant?.name || '—'}</dd>
            <dt>Rôle</dt>
            <dd className="mono">{role || '—'}</dd>
            <dt>Espaces</dt>
            <dd>
              {tenants.map((item) => (
                <span key={item.id} className="badge badge-pending">
                  {item.name} · {item.role}
                </span>
              ))}
            </dd>
          </dl>
          <button type="button" className="btn btn-secondary mt-8" onClick={signOut}>
            Se déconnecter
          </button>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>Routeur x86 dans VirtualBox</h2>
          </div>
          <ol className="steps">
            <li>
              Réseau de la VM en <strong>accès par hôte</strong> (host-only), par exemple
              <code>192.168.56.101/24</code>.
            </li>
            <li>
              Sur le routeur, activez l'API REST et un utilisateur dédié :
              <pre className="script script-inline">
{`/ip service enable www-ssl
/user group add name=kora policy=read,write,api,rest-api,test
/user add name=kora group=kora password=<mot-de-passe>`}
              </pre>
            </li>
            <li>
              Testez depuis la machine hôte, sans passer par cette console :
              <pre className="script script-inline">
{`cd backend
python manage.py probe_router --host 192.168.56.101 \\
  --username kora --password <mot-de-passe>`}
              </pre>
            </li>
            <li>
              Puis, sur la fiche du routeur : <em>Connecter le routeur</em> → identifiants →
              <em> Tester la connexion</em>.
            </li>
          </ol>
          <p className="muted small">
            Le certificat du routeur est auto-signé : la vérification TLS est désactivée par défaut
            (<code>MIKROTIK_VERIFY_TLS=0</code>). En HTTP simple, utilisez le port 80 et décochez HTTPS.
          </p>
        </div>
      </div>
    </section>
  );
}
