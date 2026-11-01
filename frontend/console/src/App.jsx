import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthProvider.jsx';
import Layout from './components/Layout.jsx';
import LoginPage from './pages/LoginPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import DevicesPage from './pages/DevicesPage.jsx';
import DevicePage from './pages/DevicePage.jsx';
import VouchersPage from './pages/VouchersPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';

/**
 * Applique la garde d'authentification et déclare les routes.
 *
 * @returns {JSX.Element} L'application.
 */
function Shell() {
  const { status } = useAuth();

  if (status === 'loading') {
    return <div className="splash">Chargement de la console…</div>;
  }
  if (status === 'anonymous') {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="devices" element={<DevicesPage />} />
        <Route path="devices/:id" element={<DevicePage />} />
        <Route path="vouchers" element={<VouchersPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

/**
 * Point d'entrée de la console : routeur (HashRouter, donc aucun réglage serveur)
 * et fournisseur d'authentification.
 *
 * @returns {JSX.Element} L'application complète.
 */
export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Shell />
      </HashRouter>
    </AuthProvider>
  );
}
