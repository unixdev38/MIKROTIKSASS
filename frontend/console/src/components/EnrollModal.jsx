import { useState } from 'react';

/**
 * Affiche le script d'enrôlement à usage unique (copie et téléchargement).
 *
 * @param {{device: object, script: string, expiresAt: string, isRenewal: boolean, onClose: Function}} props
 *   Routeur, script renvoyé par l'API et rappel de fermeture.
 * @returns {JSX.Element} La modale.
 */
export default function EnrollModal({ device, script, expiresAt, isRenewal, onClose }) {
  const [copied, setCopied] = useState(false);

  /** Copie le script dans le presse-papiers, avec repli si l'API est indisponible. */
  async function copy() {
    try {
      await navigator.clipboard.writeText(script);
    } catch {
      const area = document.createElement('textarea');
      area.value = script;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      document.body.removeChild(area);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  /** Télécharge le script au format `.rsc` (importable dans RouterOS). */
  function download() {
    const blob = new Blob([script], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `kora-${device.name.replace(/[^\w-]+/g, '-').toLowerCase()}.rsc`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const expiry = expiresAt ? new Date(expiresAt).toLocaleString('fr-FR') : '—';

  return (
    <div className="modal-backdrop" onMouseDown={onClose} role="presentation">
      <div
        className="modal modal-wide"
        role="dialog"
        aria-modal="true"
        aria-label="Script d'enrôlement"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-head">
          <h2>{isRenewal ? 'Nouveau script (rotation)' : "Script d'enrôlement"}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Fermer">
            ×
          </button>
        </header>

        <div className="modal-body">
          <p className="alert alert-warn">
            Ce script contient le mot de passe du routeur. Il ne sera <strong>plus jamais affiché</strong> :
            copiez-le maintenant (expire le {expiry}).
          </p>
          <pre className="script">{script}</pre>
          <p className="muted small">
            Application : <code>/tool fetch url="…" dst-path=kora.rsc</code> puis{' '}
            <code>/import file=kora.rsc</code>, ou collez le contenu dans la fenêtre Terminal de
            WinBox.
          </p>
        </div>

        <footer className="modal-foot">
          <button type="button" className="btn btn-secondary" onClick={download}>
            Télécharger .rsc
          </button>
          <button type="button" className="btn btn-primary" onClick={copy}>
            {copied ? 'Copié ✓' : 'Copier le script'}
          </button>
        </footer>
      </div>
    </div>
  );
}
