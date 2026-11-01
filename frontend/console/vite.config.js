import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Développement : le serveur écoute sur toutes les interfaces (aperçu distant) et
 * relaie `/api` vers Django, ce qui évite tout problème de CORS.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },
  preview: { host: '0.0.0.0', port: 4173, allowedHosts: true },
});
