"""Écrans de pilotage : tableau de bord, parc, détail routeur, sessions."""
from kit import (area_chart, badge, bar_chart, crumb, icon, shell, sparkline, status_badge)


def dashboard() -> str:
    ca = [38000, 52000, 47000, 61000, 58000, 74000, 69000, 81000, 66000,
          92000, 78000, 84000, 71000, 84500]
    labels = ["18/10", "20/10", "22/10", "24/10", "26/10", "28/10", "30/10", "01/11"]

    devices = [
        ("hAP-ac2 · cyber-centre", "7.16.2", "Cyber Centre-ville", "En ligne", 18, "il y a 12 s"),
        ("hAP-lite · cyber-ouaga2000", "7.14.3", "Ouaga 2000", "Dégradé", 9, "il y a 4 min"),
        ("RB4011 · résidence-kossodo", "7.18.1", "Kossodo", "En ligne", 6, "il y a 31 s"),
        ("CHR · hôtel-indépendance", "7.11.2", "Hôtel Indépendance", "Hors ligne", 0, "il y a 3 h 12"),
    ]
    rows = "".join(
        f'<tr><td><div class="cell-strong">{n}</div><div class="cell-sub mono">ROS {v}</div></td>'
        f'<td>{s}</td><td>{status_badge(st)}</td><td class="right num">{c}</td>'
        f'<td class="right muted nowrap">{seen}</td></tr>'
        for n, v, s, st, c, seen in devices)

    payments = [
        ("Voucher 24 h", "KAD-7734", "500 FCFA", "Orange Money", "il y a 2 min"),
        ("Voucher 1 h", "KAD-1190", "200 FCFA", "Espèces", "il y a 9 min"),
        ("Voucher 7 j", "KAD-4821", "2 000 FCFA", "Wave", "il y a 26 min"),
        ("Voucher 24 h", "KAD-2287", "500 FCFA", "Moov Money", "il y a 41 min"),
    ]
    pay_html = "".join(
        f'<div class="list-item"><div class="li-icon ok">{icon("check", 15)}</div>'
        f'<div class="grow"><div class="li-title">{t} <span class="mono muted">· {c}</span></div>'
        f'<div class="li-sub">{m} · {w}</div></div>'
        f'<div class="strong num">{a}</div></div>'
        for t, c, a, m, w in payments)

    content = f'''
<div class="banner banner-danger">{icon("warning", 16)}
  <div class="grow"><b>2 alertes ouvertes</b> — « Hôtel Indépendance » est hors ligne depuis 3 h 12,
  et le stockage de « cyber-ouaga2000 » est à 91 %.</div>
  <a class="btn btn-sm btn-secondary" href="devices.html">Voir</a>
</div>

<div class="grid grid-4 mt-16">
  <div class="card kpi">
    <div class="kpi-label">{icon("cash", 14)} Recette du jour</div>
    <div class="kpi-value num">84 500 <small>FCFA</small></div>
    <div class="kpi-foot"><span class="delta up">▲ 12,4 %</span> vs hier · 143 ventes</div>
  </div>
  <div class="card kpi">
    <div class="kpi-label">{icon("wifi", 14)} Sessions actives</div>
    <div class="kpi-value num">37</div>
    <div class="kpi-foot">{sparkline([12, 18, 15, 24, 21, 30, 27, 34, 31, 37])}<span>pic : 42</span></div>
  </div>
  <div class="card kpi">
    <div class="kpi-label">{icon("router", 14)} Routeurs en ligne</div>
    <div class="kpi-value num">9 <small>/ 11</small></div>
    <div class="kpi-foot"><span class="delta down">▼ 2</span> à vérifier</div>
  </div>
  <div class="card kpi">
    <div class="kpi-label">{icon("tag", 14)} Vouchers en stock</div>
    <div class="kpi-value num">1 248</div>
    <div class="kpi-foot">valeur faciale : <b>386 400 FCFA</b></div>
  </div>
</div>

<div class="grid grid-main mt-16">
  <div class="card">
    <div class="card-head">
      <div><div class="card-title">Recette des 14 derniers jours</div>
      <div class="card-sub">Ventes de vouchers, tous sites confondus</div></div>
      <div class="row"><span class="badge badge-brand">FCFA</span>
      <button class="btn btn-sm btn-secondary">{icon("download", 14)} Export</button></div>
    </div>
    <div class="card-body">{area_chart(ca, labels=labels)}</div>
  </div>
  <div class="card" id="alertes">
    <div class="card-head"><div class="card-title">Alertes</div>{badge("2 ouvertes", "badge-danger")}</div>
    <div class="list">
      <div class="list-item"><div class="li-icon danger">{icon("power", 15)}</div>
        <div class="grow"><div class="li-title">Routeur hors ligne</div>
        <div class="li-sub">hôtel-indépendance · 3 h 12</div></div>
        <button class="btn btn-sm btn-secondary">Acquitter</button></div>
      <div class="list-item"><div class="li-icon warn">{icon("warning", 15)}</div>
        <div class="grow"><div class="li-title">Stockage &gt; 90 %</div>
        <div class="li-sub">cyber-ouaga2000 · 91 % de 16 Mo</div></div>
        <button class="btn btn-sm btn-secondary">Acquitter</button></div>
      <div class="list-item"><div class="li-icon ok">{icon("check", 15)}</div>
        <div class="grow"><div class="li-title">Quota atteint (résolu)</div>
        <div class="li-sub">KAD-2287 · il y a 2 h</div></div>
        <span class="muted small">Résolue</span></div>
    </div>
  </div>
</div>

<div class="grid grid-main mt-16">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Parc MikroTik</div>
      <div class="card-sub">11 routeurs · 6 sites</div></div>
      <a class="btn btn-sm btn-secondary" href="devices.html">Tout voir {icon("arrow", 14)}</a></div>
    <div class="table-wrap"><table class="table"><thead><tr>
      <th>Routeur</th><th>Site</th><th>Statut</th><th class="right">Clients</th>
      <th class="right">Dernier contact</th></tr></thead><tbody>{rows}</tbody></table></div>
  </div>
  <div class="card">
    <div class="card-head"><div class="card-title">Derniers encaissements</div>
      <a class="btn btn-sm btn-ghost" href="cashier.html">Caisse {icon("arrow", 14)}</a></div>
    <div class="list">{pay_html}</div>
  </div>
</div>
'''
    return shell(
        "Tableau de bord", "dashboard.html", content, crumbs=crumb("Espace de travail", "Tableau de bord"),
        page_title="Bonjour Ali 👋",
        page_sub="Voici la situation de votre réseau aujourd'hui, samedi 1er novembre.",
        actions=(f'<button class="btn btn-secondary">{icon("refresh", 15)} Actualiser</button>'
                 f'<a class="btn btn-primary" href="cashier.html">{icon("cash", 15)} Vendre un voucher</a>'))


def devices() -> str:
    data = [
        ("hAP-ac2 · cyber-centre", "CC-HAP-01", "Cyber Centre-ville", "Ouagadougou", "7.16.2",
         "10.66.1.14", "En ligne", 18, 24, "il y a 12 s"),
        ("hAP-lite · cyber-ouaga2000", "CC-HAP-02", "Ouaga 2000", "Ouagadougou", "7.14.3",
         "10.66.1.15", "Dégradé", 9, 91, "il y a 4 min"),
        ("RB4011 · résidence-kossodo", "RK-RB-01", "Kossodo", "Ouagadougou", "7.18.1",
         "10.66.1.20", "En ligne", 6, 12, "il y a 31 s"),
        ("CHR · hôtel-indépendance", "HI-CHR-01", "Hôtel Indépendance", "Ouagadougou", "7.11.2",
         "10.66.1.31", "Hors ligne", 0, 7, "il y a 3 h 12"),
        ("hAP-ac3 · cyber-koudougou", "CK-HAP-01", "Cyber Koudougou", "Koudougou", "7.15.3",
         "10.66.1.40", "En ligne", 4, 33, "il y a 46 s"),
        ("hEX · école-nongréma", "EN-HEX-01", "École Nongrémassom", "Ouagadougou", "7.16.2",
         "10.66.1.52", "En ligne", 0, 18, "il y a 1 min"),
        ("hAP-lite · cyber-bobo", "CB-HAP-01", "Cyber Bobo", "Bobo-Dioulasso", "7.12.1",
         "10.66.1.60", "En attente", 0, 5, "jamais"),
    ]
    rows = "".join(
        f'''<tr>
          <td><div class="cell-strong">{name}</div>
              <div class="cell-sub mono">{serial} · {ip}</div></td>
          <td>{site}<div class="cell-sub">{city}</div></td>
          <td>{status_badge(status)}</td>
          <td><span class="mono">ROS {ros}</span></td>
          <td class="right num">{clients}</td>
          <td class="right"><span class="num">{disk} %</span>
              <div class="cell-sub">stockage</div></td>
          <td class="right muted nowrap">{seen}</td>
          <td class="right nowrap">
            <a class="btn btn-sm btn-ghost" href="device.html">Ouvrir</a>
            <button class="icon-btn" aria-label="Plus d'actions">{icon("gear", 15)}</button>
          </td>
        </tr>'''
        for name, serial, site, city, ros, ip, status, clients, disk, seen in data)

    content = f'''
<div class="grid grid-4">
  <div class="card kpi"><div class="kpi-label">{icon("router", 14)} Routeurs</div>
    <div class="kpi-value num">11</div><div class="kpi-foot">6 sites · 3 villes</div></div>
  <div class="card kpi"><div class="kpi-label">{icon("wifi", 14)} En ligne</div>
    <div class="kpi-value num">9</div><div class="kpi-foot">81 % du parc</div></div>
  <div class="card kpi"><div class="kpi-label">{icon("warning", 14)} Hors ligne</div>
    <div class="kpi-value num">2</div><div class="kpi-foot">1 depuis plus de 3 h</div></div>
  <div class="card kpi"><div class="kpi-label">{icon("activity", 14)} Version RouterOS</div>
    <div class="kpi-value num">7.16 <small>médiane</small></div>
    <div class="kpi-foot"><span class="delta up">▲ 4</span> mises à jour disponibles</div></div>
</div>

<div class="card mt-16">
  <div class="card-head">
    <div class="row wrap">
      <div class="input-group" style="min-width:260px">
        <input class="input" placeholder="Nom, série, IP…">
        <span class="addon">{icon("search", 15)}</span>
      </div>
      <select class="select" style="width:auto"><option>Tous les sites</option><option>Cyber Centre-ville</option><option>Ouaga 2000</option></select>
      <select class="select" style="width:auto"><option>Tous les statuts</option><option>En ligne</option><option>Hors ligne</option></select>
      <select class="select" style="width:auto"><option>Toutes les versions</option><option>7.18.x</option><option>7.16.x</option></select>
    </div>
    <div class="row">
      <button class="btn btn-secondary btn-sm">{icon("download", 14)} CSV</button>
      <a class="btn btn-primary btn-sm" href="enroll.html">{icon("plus", 14)} Ajouter un routeur</a>
    </div>
  </div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Routeur</th><th>Site</th><th>Statut</th><th>Version</th>
    <th class="right">Clients</th><th class="right">Disque</th>
    <th class="right">Dernier contact</th><th></th>
  </tr></thead><tbody>{rows}</tbody></table></div>
  <div class="row-between" style="padding:12px 16px;border-top:1px solid var(--ink-100)">
    <span class="muted small">7 routeurs affichés sur 11</span>
    <div class="row"><button class="btn btn-sm btn-secondary">Précédent</button>
      <button class="btn btn-sm btn-secondary">Suivant</button></div>
  </div>
</div>

<div class="banner banner-info mt-16">{icon("shield", 16)}
  <div class="grow">Tous les routeurs sont joints via un tunnel WireGuard : aucun port de management
  n'est exposé sur Internet. <b>4 routeurs</b> utilisent encore un certificat auto-signé ancien.</div>
  <a class="btn btn-sm btn-secondary" href="design-system.html">En savoir plus</a>
</div>
'''
    return shell(
        "Routeurs", "devices.html", content, crumbs=crumb("Réseau", "Routeurs"),
        page_title="Parc de routeurs",
        page_sub="11 routeurs sur 6 sites · supervision toutes les 60 s",
        actions=(f'<button class="btn btn-secondary">{icon("refresh", 15)} Synchroniser</button>'
                 f'<a class="btn btn-primary" href="enroll.html">{icon("plus", 15)} Ajouter un routeur</a>'))


def device() -> str:
    events = [
        ("ok", "Synchronisation réussie", "1 248 vouchers vérifiés · 3 écarts corrigés", "il y a 2 min"),
        ("warn", "Certificat bientôt expiré", "api-ssl · expire dans 21 jours", "il y a 1 h"),
        ("", "Session interrompue", "client KAD-2287 · quota atteint", "il y a 2 h"),
        ("ok", "Sauvegarde de configuration", "export de 42 Ko stocké", "hier 22:00"),
        ("danger", "Routeur injoignable", "reprise automatique après 3 min", "hier 18:41"),
    ]
    ev_html = "".join(
        f'<div class="list-item"><div class="li-icon {k}">{icon("check" if k == "ok" else "warning" if k == "warn" else "power" if k == "danger" else "activity", 15)}</div>'
        f'<div class="grow"><div class="li-title">{t}</div><div class="li-sub">{d}</div></div>'
        f'<span class="muted small nowrap">{w}</span></div>'
        for k, t, d, w in events)

    ifaces = [
        ("ether1", "WAN", "up", "1 Gbps", "92,4 Mbps", "18,7 Mbps"),
        ("bridge-hotspot", "LAN", "up", "1 Gbps", "31,2 Mbps", "4,1 Mbps"),
        ("wlan1", "Wi-Fi 2,4 GHz", "up", "300 Mbps", "12,8 Mbps", "3,3 Mbps"),
        ("wlan2", "Wi-Fi 5 GHz", "up", "867 Mbps", "28,4 Mbps", "1,9 Mbps"),
        ("ether5", "Spare", "down", "1 Gbps", "—", "—"),
    ]
    if_html = "".join(
        f'<tr><td class="mono">{n}</td><td>{role}</td>'
        f'<td>{"<span class=badge badge-ok><span class=dot></span>up</span>" if st == "up" else "<span class=badge><span class=dot></span>down</span>"}</td>'
        f'<td class="right muted">{sp}</td><td class="right num">{rx}</td>'
        f'<td class="right num">{tx}</td></tr>'
        for n, role, st, sp, rx, tx in ifaces)

    content = f'''
<div class="card">
  <div class="card-body">
    <div class="row-between wrap">
      <div class="row">
        <div class="brand-mark" style="background:linear-gradient(140deg,var(--brand-400),var(--brand-700))">{icon("router", 18)}</div>
        <div>
          <div class="row"><h2 style="font-size:17px;letter-spacing:-.3px">hAP-ac² · cyber-centre</h2>
            {status_badge("En ligne")}</div>
          <div class="muted small mono">CC-HAP-01 · 10.66.1.14 · RouterOS 7.16.2 · uptime 34 j 07 h</div>
        </div>
      </div>
      <div class="row wrap">
        <button class="btn btn-secondary btn-sm">{icon("refresh", 14)} Synchroniser</button>
        <button class="btn btn-secondary btn-sm">{icon("save", 14)} Sauvegarder</button>
        <button class="btn btn-secondary btn-sm">Tester la connexion</button>
        <button class="btn btn-danger-soft btn-sm">{icon("power", 14)} Redémarrer</button>
      </div>
    </div>
  </div>
  <div class="tabs" style="padding:0 16px">
    <a class="tab active" href="#">Vue d'ensemble</a>
    <a class="tab" href="#">Interfaces</a>
    <a class="tab" href="#">Sessions <span class="count">18</span></a>
    <a class="tab" href="#">Vouchers <span class="count">312</span></a>
    <a class="tab" href="#">Configuration</a>
    <a class="tab" href="#">Événements</a>
    <a class="tab" href="#">Réglages</a>
  </div>
</div>

<div class="grid grid-4 mt-16">
  <div class="card kpi"><div class="kpi-label">Processeur</div>
    <div class="kpi-value num">18 <small>%</small></div>
    <div class="kpi-foot">{sparkline([12, 22, 18, 35, 28, 21, 17, 18])}</div></div>
  <div class="card kpi"><div class="kpi-label">Mémoire</div>
    <div class="kpi-value num">42 <small>%</small></div>
    <div class="kpi-foot">54 Mo de 128 Mo</div></div>
  <div class="card kpi"><div class="kpi-label">Clients connectés</div>
    <div class="kpi-value num">18</div>
    <div class="kpi-foot"><span class="delta up">▲ 3</span> en 10 min</div></div>
  <div class="card kpi"><div class="kpi-label">Latence plateforme</div>
    <div class="kpi-value num">38 <small>ms</small></div>
    <div class="kpi-foot">tunnel WireGuard · 31 ms aller</div></div>
</div>

<div class="grid grid-main mt-16">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Trafic des interfaces</div>
      <div class="card-sub">Débit descendant · agrégé sur 1 h</div></div>
      <div class="row"><span class="badge badge-brand">Mbps</span>
        <select class="select" style="width:auto;height:30px;font-size:12.5px">
          <option>1 heure</option><option>24 heures</option><option>7 jours</option></select></div>
    </div>
    <div class="card-body">{area_chart([22, 38, 30, 52, 74, 61, 88, 92, 71, 54, 63, 84], height=200,
                                      labels=["12:00", "12:15", "12:30", "12:45", "13:00"])}</div>
    <div class="table-wrap"><table class="table compact"><thead><tr>
      <th>Interface</th><th>Rôle</th><th>État</th><th class="right">Débit</th>
      <th class="right">↓ actuel</th><th class="right">↑ actuel</th></tr></thead><tbody>{if_html}</tbody></table></div>
  </div>
  <div class="stack">
    <div class="card">
      <div class="card-head"><div class="card-title">Santé</div>{badge("Bon", "badge-ok")}</div>
      <div class="card-body stack">
        <div class="row-between"><span class="muted small">Stockage</span>
          <span class="num strong">24 % de 16 Mo</span></div>
        <div class="row-between"><span class="muted small">Température</span>
          <span class="num strong">41 °C</span></div>
        <div class="row-between"><span class="muted small">Alerte disque</span>
          <span class="num strong">non</span></div>
        <div class="row-between"><span class="muted small">Certificat api-ssl</span>
          <span class="strong" style="color:var(--warn-600)">21 jours</span></div>
        <div class="row-between"><span class="muted small">Mise à jour</span>
          <span class="strong" style="color:var(--brand-700)">7.18.1 dispo</span></div>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><div class="card-title">Derniers événements</div>
        <a class="btn btn-sm btn-ghost" href="#">Tout voir</a></div>
      <div class="list">{ev_html}</div>
    </div>
  </div>
</div>
'''
    return shell("hAP-ac² · cyber-centre", "devices.html", content,
                 crumbs=f'<span>Réseau</span> {icon("arrow", 12)} <a href="devices.html">Routeurs</a> {icon("arrow", 12)} <b>hAP-ac² · cyber-centre</b>')


def sessions() -> str:
    data = [
        ("KAD-7734", "client 24 h", "10.5.50.113", "A4:2B:8C:11:9F:02", "hAP-ac2 · cyber-centre",
         "2,1 Mbps", "412 Mo", "01:12:04", "Orange Money"),
        ("KAD-1190", "client 1 h", "10.5.50.87", "D8:3A:DD:44:1C:77", "hAP-ac2 · cyber-centre",
         "0,8 Mbps", "96 Mo", "00:38:41", "Espèces"),
        ("KAD-4821", "client 7 j", "10.5.52.31", "F0:9F:C2:3B:AA:10", "RB4011 · kossodo",
         "4,6 Mbps", "3,8 Go", "18:22:15", "Wave"),
        ("KAD-2287", "client 24 h", "10.5.60.14", "2C:54:91:77:0B:E3", "CHR · hôtel",
         "1,4 Mbps", "221 Mo", "00:09:50", "Moov Money"),
        ("KAD-0912", "client 1 h", "10.5.50.201", "AC:84:C6:12:55:9D", "hAP-ac2 · cyber-centre",
         "0,3 Mbps", "31 Mo", "00:04:12", "Espèces"),
    ]
    rows = "".join(
        f'''<tr>
          <td><div class="cell-strong mono">{code}</div><div class="cell-sub">{plan}</div></td>
          <td class="mono">{ip}</td>
          <td class="mono cell-sub">{mac}</td>
          <td>{dev}</td>
          <td class="right num">{rate}</td>
          <td class="right num">{vol}</td>
          <td class="right num">{dur}</td>
          <td>{badge(pay, "badge-brand" if pay != "Espèces" else "")}</td>
          <td class="right"><button class="btn btn-sm btn-danger-soft">Déconnecter</button></td>
        </tr>'''
        for code, plan, ip, mac, dev, rate, vol, dur, pay in data)

    content = f'''
<div class="banner banner-brand">{icon("wifi", 16)}
  <div class="grow"><b>Flux temps réel</b> — les sessions se mettent à jour toutes les 10 s
  (WebSocket, repli automatique en actualisation toutes les 15 s si la connexion est instable).</div>
  {badge("Connecté", "badge-live", True)}
</div>

<div class="grid grid-4 mt-16">
  <div class="card kpi"><div class="kpi-label">{icon("activity", 14)} Sessions actives</div>
    <div class="kpi-value num">37</div><div class="kpi-foot"><span class="delta up">▲ 4</span> en 10 min</div></div>
  <div class="card kpi"><div class="kpi-label">Volume consommé (jour)</div>
    <div class="kpi-value num">12,4 <small>Go</small></div><div class="kpi-foot">{sparkline([4, 6, 5, 9, 8, 11, 10, 12])}</div></div>
  <div class="card kpi"><div class="kpi-label">Durée moyenne</div>
    <div class="kpi-value num">48 <small>min</small></div><div class="kpi-foot">médiane : 31 min</div></div>
  <div class="card kpi"><div class="kpi-label">Quota atteint (24 h)</div>
    <div class="kpi-value num">6</div><div class="kpi-foot">coupures automatiques · 0 incident</div></div>
</div>

<div class="card mt-16">
  <div class="card-head">
    <div class="row wrap">
      <div class="input-group" style="min-width:220px">
        <input class="input" placeholder="Code voucher, IP, MAC…">
        <span class="addon">{icon("search", 15)}</span>
      </div>
      <select class="select" style="width:auto"><option>Tous les routeurs</option></select>
      <select class="select" style="width:auto"><option>Toutes les offres</option></select>
    </div>
    <div class="row">{badge("37 en cours", "badge-ok", True)}
      <button class="btn btn-sm btn-secondary">{icon("download", 14)} Export</button></div>
  </div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Voucher</th><th>Adresse IP</th><th>MAC</th><th>Routeur</th>
    <th class="right">Débit</th><th class="right">Volume</th><th class="right">Durée</th>
    <th>Paiement</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="row-between" style="padding:12px 16px;border-top:1px solid var(--ink-100)">
    <span class="muted small">5 sessions affichées sur 37 · actualisé il y a 4 s</span>
    <div class="row"><button class="btn btn-sm btn-secondary">Tout déconnecter</button></div>
  </div>
</div>

<div class="grid grid-3 mt-16">
  <div class="card"><div class="card-head"><div class="card-title">Sessions par routeur</div></div>
    <div class="card-body">{bar_chart([18, 9, 6, 4, 0], ["cyber-centre", "ouaga2000", "kossodo", "koudougou", "hôtel"], height=150)}</div></div>
  <div class="card"><div class="card-head"><div class="card-title">Consommation horaire</div></div>
    <div class="card-body">{bar_chart([2, 1, 1, 3, 4, 6, 9, 12, 8, 7, 5, 3], ["0h", "3h", "6h", "9h", "12h", "15h", "18h", "21h"], height=150)}</div></div>
  <div class="card"><div class="card-head"><div class="card-title">À surveiller</div>
      {badge("1", "badge-warn")}</div>
    <div class="list">
      <div class="list-item"><div class="li-icon warn">{icon("warning", 15)}</div>
        <div class="grow"><div class="li-title">Session longue</div>
        <div class="li-sub">KAD-4821 · 18 h 22 · vérifier le partage</div></div></div>
      <div class="list-item"><div class="li-icon ok">{icon("check", 15)}</div>
        <div class="grow"><div class="li-title">3 déconnexions testées</div>
        <div class="li-sub">CoA + API, effet en 1,4 s</div></div></div>
      <div class="list-item"><div class="li-icon">{icon("clock", 15)}</div>
        <div class="grow"><div class="li-title">Prochain relevé</div>
        <div class="li-sub">Interim-Update toutes les 5 min</div></div></div>
    </div>
  </div>
</div>
'''
    return shell("Sessions actives", "sessions.html", content,
                 crumbs=crumb("Réseau", "Sessions actives"),
                 page_title="Sessions actives",
                 page_sub="37 clients connectés · mise à jour temps réel",
                 actions=(f'<button class="btn btn-secondary">{icon("refresh", 15)} Actualiser</button>'
                          f'<a class="btn btn-secondary" href="vouchers.html">{icon("ticket", 15)} Vouchers</a>'))
