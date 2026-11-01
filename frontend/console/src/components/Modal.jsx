import { useEffect } from 'react';

/**
 * Fenêtre modale accessible (fermeture par Échap ou clic sur le fond).
 *
 * @param {{title: string, onClose: Function, children: React.ReactNode, footer?: React.ReactNode}} props
 *   Titre, action de fermeture, contenu et pied optionnel.
 * @returns {JSX.Element} La modale.
 */
export default function Modal({ title, onClose, children, footer }) {
  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-head">
          <h2>{title}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Fermer">
            ×
          </button>
        </header>
        <div className="modal-body">{children}</div>
        {footer ? <footer className="modal-foot">{footer}</footer> : null}
      </div>
    </div>
  );
}
