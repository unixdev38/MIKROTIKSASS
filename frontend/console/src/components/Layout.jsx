import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider.jsx';

const NAV = [
  { to: '/', label: 'Tableau de bord', end: true },
  { to: '/devices', label: 'Routeurs' },
  { to: '/vouchers', label: 'Vouchers' },
  { to: '/settings', label: 'Réglages' },
];

/**
 * Coquille de l'application : navigation latérale, en-tête et zone de contenu.
 *
 * @returns {JSX.Element} La mise en page.
 */
export default function Layout() {
  const { user, tenant, role, signOut } = useAuth();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">K</span>
          <span>
            <strong>Kora</strong>
            <small>console</small>
          </span>
        </div>
        <nav className="nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="workspace">
            <span className="workspace-name">{tenant?.name || 'Aucun espace'}</span>
            <span className="workspace-role">{role || '—'}</span>
          </div>
          <button type="button" className="btn btn-ghost" onClick={signOut}>
            Se déconnecter
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <span className="muted small">Espace de travail</span>
            <strong>{tenant?.name || '—'}</strong>
          </div>
          <div className="topbar-user">
            <span className="avatar">{initials(user?.full_name)}</span>
            <div>
              <strong>{user?.full_name}</strong>
              <small className="muted">{user?.email}</small>
            </div>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

/**
 * Extrait les initiales d'un nom complet.
 *
 * @param {string} [name] Nom affiché.
 * @returns {string} Une ou deux lettres.
 */
function initials(name) {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('');
}
