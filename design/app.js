/* KORA — micro-interactions du prototype (aucune dépendance). */
document.addEventListener('click', (e) => {
  const copy = e.target.closest('.code-copy');
  if (copy) {
    const block = copy.closest('.code-block');
    const text = block ? block.innerText.replace(/^Copier$|^Copié$/gm, '').trim() : '';
    navigator.clipboard?.writeText(text);
    copy.textContent = 'Copié ✓';
    setTimeout(() => { copy.textContent = 'Copier'; }, 1800);
  }

  const tab = e.target.closest('.tab[data-tab]');
  if (tab) {
    e.preventDefault();
    const group = tab.closest('.tabs');
    group.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    const scope = document.querySelector('[data-tab-scope]');
    if (scope) {
      scope.querySelectorAll('[data-panel]').forEach((p) => {
        p.classList.toggle('hidden', p.dataset.panel !== tab.dataset.tab);
      });
    }
  }

  const plan = e.target.closest('.plan-option');
  if (plan) {
    plan.parentElement.querySelectorAll('.plan-option').forEach((p) => p.classList.remove('selected'));
    plan.classList.add('selected');
  }

  const pm = e.target.closest('.pay-method');
  if (pm) {
    pm.parentElement.querySelectorAll('.pay-method').forEach((p) => p.classList.remove('selected'));
    pm.classList.add('selected');
  }

  const sw = e.target.closest('.switch');
  if (sw) sw.classList.toggle('on');
});

/* Démo : le bouton « Encaisser » affiche le ticket. */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('[data-demo="encaisser"]');
  const ticket = document.querySelector('[data-demo-target="ticket"]');
  if (btn && ticket) {
    btn.addEventListener('click', () => {
      ticket.classList.remove('hidden');
      ticket.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  }
  const wait = document.querySelector('[data-demo="enroll-wait"]');
  if (wait) {
    setTimeout(() => {
      wait.innerHTML = '<span class="badge badge-ok"><span class="dot"></span>Connecté</span>'
        + '<span class="muted small">hAP ac² · RouterOS 7.16.2 · 1,2 s</span>'
        + '<a class="btn btn-sm btn-primary" href="devices.html">Voir le routeur</a>';
    }, 2200);
  }
});
