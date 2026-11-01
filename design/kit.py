"""Composants partagés des maquettes : icônes, graphiques, QR, coquille de page."""
from __future__ import annotations

import random

ICONS: dict[str, str] = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "router": '<rect x="2.5" y="13" width="19" height="7" rx="2"/><path d="M6 16.5h.01M9.5 16.5h.01"/><path d="M12 10V6M8.5 6.5a5 5 0 0 1 7 0M6 4a8.5 8.5 0 0 1 12 0"/>',
    "activity": '<path d="M3 12h4l2.5-6 4 12L16 12h5"/>',
    "bell": '<path d="M18 8a6 6 0 1 0-12 0c0 6-2 7-2 7h16s-2-1-2-7"/><path d="M10.5 20a2 2 0 0 0 3 0"/>',
    "tag": '<path d="M20.6 12.6 12 21.2l-9-9V3h9.2l8.4 8.4a1.4 1.4 0 0 1 0 1.2Z"/><circle cx="7.5" cy="7.5" r="1.4"/>',
    "ticket": '<path d="M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2 2.5 2.5 0 0 0 0 5 2 2 0 0 1-2 2H5a2 2 0 0 1-2-2 2.5 2.5 0 0 0 0-5Z"/><path d="M9 8v8M15 8v8" stroke-dasharray="2 3"/>',
    "wallet": '<rect x="2.5" y="6" width="19" height="13" rx="2.5"/><path d="M2.5 10h19"/><circle cx="17" cy="14.5" r="1.2"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 5.5a3.2 3.2 0 0 1 0 6M18 20a6 6 0 0 0-2-4.4"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 3 15a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.4-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 10 4.6a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 21 11a2 2 0 1 1 0 4 1.7 1.7 0 0 0-1.6 0Z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "download": '<path d="M12 3v12M7.5 10.5 12 15l4.5-4.5"/><path d="M4 20h16"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
    "copy": '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>',
    "check": '<path d="m4 12.5 5 5L20 6.5"/>',
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "power": '<path d="M12 3v9"/><path d="M6.5 7a8 8 0 1 0 11 0"/>',
    "save": '<path d="M12 3v12l4-4M12 15l-4-4"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "wifi": '<path d="M2.5 8.5a15 15 0 0 1 19 0M6 12.5a10 10 0 0 1 12 0M9.5 16.2a5 5 0 0 1 5 0"/><circle cx="12" cy="19.5" r="1"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/>',
    "chart": '<path d="M4 20V9M10 20V4M16 20v-7M22 20H2"/>',
    "shield": '<path d="M12 3 4.5 6v6c0 4.5 3.2 7.6 7.5 9 4.3-1.4 7.5-4.5 7.5-9V6Z"/><path d="m9 12 2 2 4-4"/>',
    "terminal": '<rect x="2.5" y="4" width="19" height="16" rx="2.5"/><path d="m7 9 3 3-3 3M13 15h4"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
    "cash": '<rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 12h.01M18 12h.01"/>',
    "warning": '<path d="M12 4 2.8 20h18.4Z"/><path d="M12 10v4M12 17.2h.01"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
}


def icon(name: str, size: int = 16, cls: str = "") -> str:
    body = ICONS.get(name, ICONS["grid"])
    return (
        f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )


_chart_id = 0


def area_chart(values: list[int], width: int = 660, height: int = 190,
               labels: list[str] | None = None) -> str:
    global _chart_id
    _chart_id += 1
    gid = f"grad{_chart_id}"
    pad_l, pad_r, pad_t, pad_b = 34, 8, 12, 22
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    vmax = max(values) * 1.15 or 1
    pts = [(pad_l + w * i / max(1, len(values) - 1),
            pad_t + h - h * v / vmax) for i, v in enumerate(values)]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = f"{line} L{pts[-1][0]:.1f},{pad_t + h:.1f} L{pts[0][0]:.1f},{pad_t + h:.1f} Z"
    grid = "".join(
        f'<line class="grid-line" x1="{pad_l}" x2="{width - pad_r}" '
        f'y1="{pad_t + h * k / 4:.1f}" y2="{pad_t + h * k / 4:.1f}"/>' for k in range(5))
    ylab = "".join(
        f'<text class="axis-label" x="{pad_l - 6}" y="{pad_t + h - h * k / 4 + 3:.1f}" '
        f'text-anchor="end">{int(vmax * k / 4 / 1000)}k</text>' for k in range(5))
    xlab = ""
    if labels:
        step = max(1, len(labels) // 6)
        for i, lab in enumerate(labels):
            if i % step == 0:
                x = pad_l + w * i / max(1, len(labels) - 1)
                xlab += f'<text class="axis-label" x="{x:.1f}" y="{height - 5}" text-anchor="middle">{lab}</text>'
    x, y = pts[-1]
    return f'''<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Évolution sur la période">
  <defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0fa37f" stop-opacity=".26"/>
    <stop offset="100%" stop-color="#0fa37f" stop-opacity="0"/>
  </linearGradient></defs>
  {grid}{ylab}{xlab}
  <path d="{area}" fill="url(#{gid})"/>
  <path class="line" d="{line}"/>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#fff" stroke="var(--brand-600)" stroke-width="2"/>
</svg>'''


def bar_chart(values: list[int], labels: list[str], width: int = 620, height: int = 160) -> str:
    pad_l, pad_r, pad_t, pad_b = 30, 6, 10, 24
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    vmax = max(values) or 1
    bw = w / len(values) * 0.56
    bars = ""
    for i, v in enumerate(values):
        x = pad_l + w * (i + 0.5) / len(values) - bw / 2
        bh = max(2, h * v / vmax)
        bars += (f'<rect class="bar{" alt" if v == 0 else ""}" x="{x:.1f}" y="{pad_t + h - bh:.1f}" '
                 f'width="{bw:.1f}" height="{bh:.1f}" rx="3"/>')
    gl = "".join(
        f'<line class="grid-line" x1="{pad_l}" x2="{width - pad_r}" '
        f'y1="{pad_t + h * k / 3:.1f}" y2="{pad_t + h * k / 3:.1f}"/>' for k in range(4))
    xl = "".join(
        f'<text class="axis-label" x="{pad_l + w * (i + .5) / len(values):.1f}" y="{height - 7}" '
        f'text-anchor="middle">{lab}</text>' for i, lab in enumerate(labels))
    return f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Histogramme">{gl}{bars}{xl}</svg>'


def sparkline(values: list[int], width: int = 88, height: int = 26) -> str:
    vmax, vmin = max(values), min(values)
    rng = (vmax - vmin) or 1
    pts = [(width * i / max(1, len(values) - 1),
            height - (height - 4) * (v - vmin) / rng - 2) for i, v in enumerate(values)]
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    return (f'<svg class="spark" viewBox="0 0 {width} {height}" aria-hidden="true">'
            f'<path d="{d}" fill="none" stroke="var(--brand-500)" stroke-width="1.8" '
            f'stroke-linecap="round"/></svg>')


def qr_svg(seed: str = "KORA-4821", size: int = 108) -> str:
    """Faux QR déterministe : visuel uniquement, jamais scannable."""
    rnd = random.Random(seed)
    n, cell = 21, size / 21
    cells = []
    for y in range(n):
        for x in range(n):
            if (x < 7 and y < 7) or (x >= n - 7 and y < 7) or (x < 7 and y >= n - 7):
                continue
            if rnd.random() > 0.52:
                cells.append(f'<rect x="{x * cell:.2f}" y="{y * cell:.2f}" '
                             f'width="{cell:.2f}" height="{cell:.2f}"/>')
    finder = []
    for ox, oy in ((0, 0), (n - 7, 0), (0, n - 7)):
        finder.append(
            f'<rect x="{ox * cell:.2f}" y="{oy * cell:.2f}" width="{7 * cell:.2f}" height="{7 * cell:.2f}"/>'
            f'<rect x="{(ox + 1) * cell:.2f}" y="{(oy + 1) * cell:.2f}" '
            f'width="{5 * cell:.2f}" height="{5 * cell:.2f}" fill="#fff"/>'
            f'<rect x="{(ox + 2) * cell:.2f}" y="{(oy + 2) * cell:.2f}" '
            f'width="{3 * cell:.2f}" height="{3 * cell:.2f}"/>')
    return (f'<svg class="qr" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" '
            f'aria-label="QR code du voucher"><rect width="{size}" height="{size}" fill="#fff"/>'
            f'<g fill="#0b1220">{"".join(cells)}{"".join(finder)}</g></svg>')


def badge(text: str, kind: str = "", dot: bool = False) -> str:
    d = '<span class="dot"></span>' if dot else ""
    return f'<span class="badge {kind}">{d}{text}</span>'


STATUS_MAP = {
    "En ligne": ("badge-ok", True), "Dégradé": ("badge-warn", True),
    "Hors ligne": ("badge-danger", True), "En attente": ("badge", True),
    "Actif": ("badge-ok", True), "Utilisé": ("badge-info", False),
    "Expiré": ("badge", False), "Révoqué": ("badge-danger", False),
    "Synchronisé": ("badge-ok", False), "Partiel": ("badge-warn", False),
    "En cours": ("badge-info", True), "Payé": ("badge-ok", False),
    "Impayé": ("badge-danger", False), "Brouillon": ("badge", False),
    "Généré": ("badge-brand", False),
}


def status_badge(status: str) -> str:
    kind, dot = STATUS_MAP.get(status, ("", False))
    return badge(status, kind, dot)


NAV = [
    ("Pilotage", [
        ("dashboard.html", "grid", "Tableau de bord", ""),
        ("devices.html", "router", "Routeurs", "11"),
        ("sessions.html", "activity", "Sessions actives", "37"),
        ("dashboard.html#alertes", "bell", "Alertes", "2"),
    ]),
    ("Ventes", [
        ("plans.html", "tag", "Forfaits", ""),
        ("vouchers.html", "ticket", "Vouchers", ""),
        ("cashier.html", "wallet", "Caisse", ""),
        ("settings.html", "users", "Équipe", ""),
    ]),
    ("Prototype", [
        ("portal.html", "wifi", "Portail captif", ""),
        ("design-system.html", "shield", "Design system", ""),
        ("index.html", "menu", "Toutes les maquettes", ""),
    ]),
]


def shell(title: str, active: str, content: str, crumbs: str = "", page_title: str = "",
          page_sub: str = "", actions: str = "") -> str:
    nav = ""
    for section, items in NAV:
        nav += f'<div class="nav-section">{section}</div>'
        for href, ic, label, count in items:
            cls = "nav-item active" if href.split("#")[0] == active else "nav-item"
            c = f'<span class="count{" alert" if label == "Alertes" else ""}">{count}</span>' if count else ""
            nav += f'<a class="{cls}" href="{href}">{icon(ic, 17, "ic")}<span>{label}</span>{c}</a>'

    head = ""
    if page_title:
        head = (f'<div class="page-head"><div><h1 class="page-title">{page_title}</h1>'
                f'<p class="page-sub">{page_sub}</p></div><div class="row">{actions}</div></div>')

    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Kora</title>
<meta name="description" content="Maquette statique du SaaS de gestion de parc MikroTik.">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">K</div>
      <div><div class="brand-name">Kora</div><div class="brand-sub">Cybers &amp; FAI</div></div>
      <div class="brand-switch">BF-01</div>
    </div>
    {nav}
    <div class="sidebar-foot">
      <a class="user-chip" href="settings.html">
        <div class="avatar">AK</div>
        <div class="grow"><div class="u-name">Ali Kaboré</div><div class="u-role">Propriétaire</div></div>
        {icon("gear", 16, "ic")}
      </a>
    </div>
  </aside>
  <div class="main">
    <div class="topbar">
      <div class="crumbs">{crumbs}</div>
      <div class="search">{icon("search", 15)}<span>Rechercher un routeur, un voucher…</span><kbd>⌘K</kbd></div>
      <button class="icon-btn" aria-label="Notifications">{icon("bell", 17)}<span class="ping"></span></button>
      <button class="icon-btn" aria-label="Console">{icon("terminal", 17)}</button>
      <div class="avatar">AK</div>
    </div>
    <div class="content">
      {head}
      {content}
    </div>
  </div>
</div>
<script src="app.js"></script>
</body>
</html>'''


def standalone(title: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Kora</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
{body}
<script src="app.js"></script>
</body>
</html>'''


def crumb(section: str, current: str) -> str:
    return f'<span>{section}</span> {icon("arrow", 12)} <b>{current}</b>'
