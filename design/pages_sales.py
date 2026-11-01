"""Écrans de vente : forfaits, vouchers, caisse, équipe & audit."""
from kit import (badge, bar_chart, crumb, icon, qr_svg, shell, sparkline, status_badge)


def plans() -> str:
    plans = [
        ("1 heure", "Accès rapide", 200, "1 h", "—", "2 Mbps", "12", True),
        ("24 heures", "Le plus vendu", 500, "24 h", "2 Go", "3 Mbps", "48", True),
        ("7 jours", "Semaine complète", 2000, "7 j", "15 Go", "5 Mbps", "31", True),
        ("30 jours", "Abonnement mensuel", 10000, "30 j", "60 Go", "10 Mbps", "8", False),
    ]
    cards = ""
    for name, desc, price, duration, quota, rate, sold, synced in plans:
        fmt_price = f"{price:,}".replace(",", "\u202f")
        cards += f'''<div class="card">
          <div class="card-head">
            <div><div class="card-title">{name}</div><div class="card-sub">{desc}</div></div>
            {badge("Synchronisé", "badge-ok", False) if synced else badge("À pousser", "badge-warn", False)}
          </div>
          <div class="card-body stack">
            <div class="row-between"><span class="muted small">Prix</span>
              <span class="num strong" style="font-size:20px">{fmt_price} FCFA</span></div>
            <div class="row-between"><span class="muted small">Validité</span>
              <span class="strong">{duration}</span></div>
            <div class="row-between"><span class="muted small">Quota</span>
              <span class="strong">{quota}</span></div>
            <div class="row-between"><span class="muted small">Débit max</span>
              <span class="strong">{rate}</span></div>
            <div class="row-between"><span class="muted small">Vendus (30 j)</span>
              <span class="strong num">{sold}</span></div>
            <div class="row-between"><span class="muted small">Profil routeur</span>
              <span class="mono small">hs-{name.split()[0]}-{rate.split()[0]}</span></div>
            <div class="row" style="margin-top:4px">
              <button class="btn btn-secondary btn-sm grow">Modifier</button>
              <button class="btn btn-primary btn-sm grow">{icon("ticket", 14)} Générer</button>
            </div>
          </div>
        </div>'''


    content = f'''
<div class="banner banner-info">{icon("tag", 16)}
  <div class="grow">Chaque forfait correspond à un <b>profil hotspot</b> sur le routeur. Un forfait modifié
  est repoussé automatiquement sur les routeurs concernés (tâche rejouable, sans doublon).</div>
  <a class="btn btn-sm btn-secondary" href="#">Voir la réconciliation</a>
</div>

<div class="grid grid-4 mt-16">{cards}</div>

<div class="grid grid-main mt-16">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Performance des offres</div>
      <div class="card-sub">Chiffre d'affaires par forfait, 30 derniers jours</div></div>
      {badge("FCFA", "badge-brand")}</div>
    <div class="card-body">{bar_chart([1440, 8650, 6200, 8000], ["1 h", "24 h", "7 j", "30 j"], height=170)}</div>
    <div class="table-wrap"><table class="table compact"><thead><tr>
      <th>Forfait</th><th class="right">Vendus</th><th class="right">CA</th>
      <th class="right">Panier moyen</th><th class="right">Taux d'usage</th></tr></thead><tbody>
      <tr><td class="cell-strong">1 heure</td><td class="right num">72</td><td class="right num">14 400</td>
        <td class="right num">200</td><td class="right">96 %</td></tr>
      <tr><td class="cell-strong">24 heures</td><td class="right num">173</td><td class="right num">86 500</td>
        <td class="right num">500</td><td class="right">91 %</td></tr>
      <tr><td class="cell-strong">7 jours</td><td class="right num">31</td><td class="right num">62 000</td>
        <td class="right num">2 000</td><td class="right">74 %</td></tr>
      <tr><td class="cell-strong">30 jours</td><td class="right num">8</td><td class="right num">80 000</td>
        <td class="right num">10 000</td><td class="right">62 %</td></tr>
    </tbody></table></div>
  </div>
  <div class="card">
    <div class="card-head"><div class="card-title">Réglages d'un forfait</div></div>
    <div class="card-body stack">
      <div class="field"><label class="label">Nom affiché au client</label>
        <input class="input" value="24 heures — 3 Mbps"></div>
      <div class="grid grid-2">
        <div class="field"><label class="label">Prix (FCFA)</label>
          <div class="input-group"><input class="input" value="500"><span class="addon">FCFA</span></div></div>
        <div class="field"><label class="label">Validité</label>
          <div class="input-group"><input class="input" value="24"><span class="addon">heures</span></div></div>
      </div>
      <div class="grid grid-2">
        <div class="field"><label class="label">Quota</label>
          <div class="input-group"><input class="input" value="2"><span class="addon">Go</span></div></div>
        <div class="field"><label class="label">Débit descendant</label>
          <div class="input-group"><input class="input" value="3"><span class="addon">Mbps</span></div></div>
      </div>
      <div class="field"><label class="label">Profil hotspot RouterOS</label>
        <select class="select"><option>hs-24h-3m</option><option>default</option></select>
        <span class="hint">Le profil est créé ou mis à jour sur le routeur à l'enregistrement.</span></div>
      <div class="row-between"><span class="label">Achetable en ligne</span>
        <div class="switch on" role="switch" aria-checked="true"></div></div>
      <div class="row"><button class="btn btn-secondary grow">Annuler</button>
        <button class="btn btn-primary grow">Enregistrer</button></div>
    </div>
  </div>
</div>
'''
    return shell("Forfaits", "plans.html", content, crumbs=crumb("Ventes", "Forfaits"),
                 page_title="Forfaits",
                 page_sub="4 offres actives · 2 000 à 10 000 FCFA",
                 actions=f'<a class="btn btn-primary" href="#">{icon("plus", 15)} Nouveau forfait</a>')


def vouchers() -> str:
    batches = [
        ("LOT-1101", "24 heures — 3 Mbps", 200, 143, "Généré", "il y a 2 j", "hAP-ac2 · cyber-centre"),
        ("LOT-1102", "1 heure — 2 Mbps", 100, 72, "Généré", "il y a 2 j", "hAP-ac2 · cyber-centre"),
        ("LOT-1103", "7 jours — 5 Mbps", 50, 31, "Partiel", "il y a 5 j", "RB4011 · kossodo"),
        ("LOT-1104", "24 heures — 3 Mbps", 300, 0, "Généré", "hier", "3 routeurs"),
    ]
    rows = "".join(
        f'''<tr><td class="cell-strong mono">{code}</td><td>{plan}</td>
        <td class="right num">{qty}</td>
        <td class="right num">{used}</td>
        <td style="min-width:110px">
          <div style="height:6px;border-radius:999px;background:var(--ink-100);overflow:hidden">
            <div style="height:100%;width:{int(used / qty * 100)}%;background:var(--brand-500)"></div></div>
          <div class="cell-sub">{int(used / qty * 100)} % utilisés</div></td>
        <td>{status_badge(st)}</td><td class="muted nowrap">{when}</td>
        <td class="small">{dev}</td>
        <td class="right nowrap">
          <a class="btn btn-sm btn-secondary" href="#">PDF</a>
          <button class="btn btn-sm btn-ghost">Détail</button></td></tr>'''
        for code, plan, qty, used, st, when, dev in batches)

    content = f'''
<div class="grid grid-main">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Générer un lot de vouchers</div>
      <div class="card-sub">Les codes sont créés en base puis poussés sur le routeur en arrière-plan</div></div>
      {badge("3 200 codes/mois", "badge-brand")}</div>
    <div class="card-body grid grid-2">
      <div class="field"><label class="label">Forfait</label>
        <select class="select"><option>24 heures — 3 Mbps (500 FCFA)</option>
          <option>1 heure — 2 Mbps (200 FCFA)</option>
          <option>7 jours — 5 Mbps (2 000 FCFA)</option></select></div>
      <div class="field"><label class="label">Quantité</label>
        <div class="input-group"><input class="input" value="100"><span class="addon">codes</span></div>
        <span class="hint">Maximum 500 par lot.</span></div>
      <div class="field"><label class="label">Préfixe (facultatif)</label>
        <input class="input" value="KAD"></div>
      <div class="field"><label class="label">Routeur cible</label>
        <select class="select"><option>hAP-ac² · cyber-centre</option>
          <option>Tous les routeurs du site</option></select></div>
      <div class="field" style="grid-column:1 / -1"><label class="label">Code offert au client</label>
        <div class="row wrap">
          <label class="row small"><input type="radio" name="cv" checked> Code seul</label>
          <label class="row small"><input type="radio" name="cv"> Code + mot de passe</label>
          <label class="row small"><input type="radio" name="cv"> Code lié à une MAC</label>
        </div></div>
      <div class="row" style="grid-column:1 / -1">
        <button class="btn btn-primary">{icon("ticket", 15)} Générer 100 vouchers</button>
        <button class="btn btn-secondary">{icon("download", 15)} Importer un CSV</button>
        <span class="hint grow">Coût d'impression estimé : 1 500 FCFA</span>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><div class="card-title">Aperçu du coupon</div>
      <span class="muted small">PDF A4 · 10 par page</span></div>
    <div class="card-body">
      <div class="ticket">
        <div class="row" style="justify-content:center;gap:8px">
          <div class="brand-mark" style="width:24px;height:24px;border-radius:7px;font-size:12px">K</div>
          <b style="font-size:12px">KORA · Cyber Centre-ville</b>
        </div>
        <div class="code">KAD-7734</div>
        <div class="small muted">24 heures · 3 Mbps · 2 Go</div>
        <div style="margin:10px 0">{qr_svg("KAD-7734", 96)}</div>
        <div class="small">Se connecter au Wi-Fi « <b>CYBER-CENTRE</b> »<br>
          puis saisir le code sur la page d'accueil.</div>
        <div class="mono small" style="margin-top:8px;color:var(--ink-400)">500 FCFA · valable 12 mois</div>
      </div>
      <div class="row mt-16"><button class="btn btn-secondary grow">{icon("download", 14)} PDF</button>
        <button class="btn btn-secondary grow">Imprimer</button></div>
      <div class="hint mt-8">Le QR ouvre directement le portail avec le code pré-rempli.</div>
    </div>
  </div>
</div>

<div class="card mt-16">
  <div class="card-head">
    <div class="row wrap">
      <div class="input-group" style="min-width:240px">
        <input class="input" placeholder="Rechercher un code (ex. KAD-7734)">
        <span class="addon">{icon("search", 15)}</span></div>
      <select class="select" style="width:auto"><option>Tous les états</option>
        <option>Non utilisé</option><option>Utilisé</option><option>Expiré</option></select>
      <select class="select" style="width:auto"><option>Tous les lots</option></select>
    </div>
    <button class="btn btn-sm btn-secondary">{icon("download", 14)} Export CSV</button>
  </div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Lot</th><th>Forfait</th><th class="right">Quantité</th><th class="right">Utilisés</th>
    <th>Consommation</th><th>État</th><th>Créé</th><th>Routeur</th><th></th>
  </tr></thead><tbody>{rows}</tbody></table></div>
</div>

<div class="grid grid-3 mt-16">
  <div class="card kpi"><div class="kpi-label">Stock disponible</div>
    <div class="kpi-value num">1 248</div>
    <div class="kpi-foot">valeur faciale 386 400 FCFA</div></div>
  <div class="card kpi"><div class="kpi-label">Taux de consommation</div>
    <div class="kpi-value num">61 <small>%</small></div>
    <div class="kpi-foot">{sparkline([40, 44, 48, 45, 52, 55, 58, 61])}</div></div>
  <div class="card kpi"><div class="kpi-label">Codes expirés (30 j)</div>
    <div class="kpi-value num">23</div>
    <div class="kpi-foot">soit 11 500 FCFA de perte évitée par alerte</div></div>
</div>
'''
    return shell("Vouchers", "vouchers.html", content, crumbs=crumb("Ventes", "Vouchers"),
                 page_title="Vouchers",
                 page_sub="4 lots · 1 248 codes disponibles",
                 actions=(f'<button class="btn btn-secondary">{icon("download", 15)} Exporter</button>'
                          f'<a class="btn btn-primary" href="#">{{icon("plus", 15)}} Nouveau lot</a>'))


def cashier() -> str:
    quick = [("1 heure", "200", "2 Mbps"), ("24 heures", "500", "3 Mbps"),
             ("7 jours", "2 000", "5 Mbps"), ("30 jours", "10 000", "10 Mbps")]
    qbtns = "".join(
        f'''<button class="btn btn-secondary" style="height:auto;padding:12px;flex-direction:column;
          align-items:flex-start;gap:2px">
          <span class="strong">{n}</span>
          <span class="mono small" style="color:var(--brand-700)">{p} FCFA</span>
          <span class="small muted">{r}</span></button>'''
        for n, p, r in quick)

    journal = [
        ("KAD-7734", "24 heures", "500", "Orange Money", "14:32"),
        ("KAD-1190", "1 heure", "200", "Espèces", "14:25"),
        ("KAD-4821", "7 jours", "2 000", "Wave", "14:18"),
        ("KAD-2287", "24 heures", "500", "Moov Money", "14:09"),
        ("KAD-0901", "1 heure", "200", "Espèces", "13:58"),
    ]
    jrows = "".join(
        f'<tr><td class="mono cell-strong">{c}</td><td>{p}</td><td class="right num">{a}</td>'
        f'<td class="small">{m}</td><td class="right muted">{t}</td></tr>'
        for c, p, a, m, t in journal)

    content = f'''
<div class="grid grid-main">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Encaisser</div>
      <div class="card-sub">3 clics : forfait → moyen de paiement → valider</div></div>
      {badge("Caisse ouverte", "badge-ok", True)}</div>
    <div class="card-body stack">
      <div class="label">1 · Choisir un forfait</div>
      <div class="grid" style="grid-template-columns:repeat(4,minmax(0,1fr))">{qbtns}</div>

      <div class="grid grid-2 mt-8">
        <div class="field"><label class="label">2 · Montant encaissé</label>
          <div class="input-group"><input class="input" value="500" style="font-size:16px;font-weight:700">
            <span class="addon">FCFA</span></div>
          <span class="hint">Modifiable (geste commercial, arrondi).</span></div>
        <div class="field"><label class="label">Téléphone du client (facultatif)</label>
          <input class="input" value="+226 70 12 34 56">
          <span class="hint">Permet d'envoyer le code par WhatsApp.</span></div>
      </div>

      <div class="field"><label class="label">3 · Moyen de paiement</label>
        <div class="row wrap">
          <label class="row small"><input type="radio" name="pm" checked> Espèces</label>
          <label class="row small"><input type="radio" name="pm"> Orange Money</label>
          <label class="row small"><input type="radio" name="pm"> Moov Money</label>
          <label class="row small"><input type="radio" name="pm"> Wave</label>
          <label class="row small"><input type="radio" name="pm"> Crédit client</label>
        </div></div>

      <div class="row mt-8">
        <button class="btn btn-primary btn-lg grow" data-demo="encaisser">
          {icon("cash", 17)} Encaisser 500 FCFA</button>
        <button class="btn btn-secondary btn-lg">Annuler</button>
      </div>
      <div class="banner banner-info">{icon("shield", 15)}
        <div class="grow">Chaque vente génère une écriture de caisse et une trace d'audit.
        Le code n'est jamais réutilisé, même en cas d'erreur de saisie.</div></div>
    </div>
  </div>

  <div class="stack">
    <div class="card" data-demo-target="ticket">
      <div class="card-head"><div class="card-title">Ticket généré</div>
        {badge("KAD-7734", "badge-brand")}</div>
      <div class="card-body">
        <div class="ticket">
          <div class="code">KAD-7734</div>
          <div class="small muted">24 heures · 3 Mbps · 2 Go</div>
          <div style="margin:8px 0">{qr_svg("KAD-7734", 92)}</div>
          <div class="row" style="justify-content:center;gap:6px">
            <button class="btn btn-sm btn-secondary">{icon("download", 13)} PDF</button>
            <button class="btn btn-sm btn-secondary">Imprimer</button>
            <button class="btn btn-sm btn-primary">WhatsApp</button>
          </div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-head"><div class="card-title">Caisse du jour</div>
        <span class="strong num">84 500 FCFA</span></div>
      <div class="list">
        <div class="list-item"><div class="li-icon ok">{icon("cash", 15)}</div>
          <div class="grow"><div class="li-title">Espèces</div>
          <div class="li-sub">31 ventes</div></div><div class="strong num">12 400</div></div>
        <div class="list-item"><div class="li-icon">{icon("phone", 15)}</div>
          <div class="grow"><div class="li-title">Orange Money</div>
          <div class="li-sub">64 ventes</div></div><div class="strong num">38 900</div></div>
        <div class="list-item"><div class="li-icon">{icon("phone", 15)}</div>
          <div class="grow"><div class="li-title">Moov Money</div>
          <div class="li-sub">29 ventes</div></div><div class="strong num">21 200</div></div>
        <div class="list-item"><div class="li-icon">{icon("phone", 15)}</div>
          <div class="grow"><div class="li-title">Wave</div>
          <div class="li-sub">19 ventes</div></div><div class="strong num">12 000</div></div>
      </div>
    </div>
  </div>
</div>

<div class="card mt-16">
  <div class="card-head"><div><div class="card-title">Journal de caisse</div>
    <div class="card-sub">Samedi 1er novembre · caissier : Ali Kaboré</div></div>
    <div class="row"><button class="btn btn-sm btn-secondary">Clôturer la caisse</button>
      <button class="btn btn-sm btn-secondary">{icon("download", 14)} Reçu Z</button></div></div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Code</th><th>Forfait</th><th class="right">Montant</th><th>Paiement</th>
    <th class="right">Heure</th><th></th></tr></thead><tbody>{jrows}</tbody></table></div>
</div>
'''
    return shell("Caisse", "cashier.html", content, crumbs=crumb("Ventes", "Caisse"),
                 page_title="Caisse",
                 page_sub="Vente de vouchers au comptoir · samedi 1er novembre",
                 actions=f'<button class="btn btn-secondary">{icon("download", 15)} Exporter la journée</button>')


def settings() -> str:
    members = [
        ("Ali Kaboré", "ali@cybercentre.bf", "Propriétaire", "Actif", "il y a 2 min"),
        ("Fatou Sawadogo", "fatou@cybercentre.bf", "Administrateur", "Actif", "il y a 1 h"),
        ("Issa Ouédraogo", "issa@install.bf", "Technicien", "Actif", "il y a 3 h"),
        ("Mariam Traoré", "caisse@cybercentre.bf", "Caissier", "Actif", "il y a 12 min"),
        ("Paul Zongo", "paul@cybercentre.bf", "Lecture seule", "Invité", "—"),
    ]
    mrows = "".join(
        f'''<tr><td><div class="row"><div class="avatar sm">{n[0]}{n.split()[-1][0]}</div>
          <div><div class="cell-strong">{n}</div><div class="cell-sub">{e}</div></div></div></td>
        <td>{badge(r, "badge-brand" if r == "Propriétaire" else "")}</td>
        <td>{badge(st, "badge-ok" if st == "Actif" else "")}</td>
        <td class="right muted">{seen}</td>
        <td class="right"><button class="btn btn-sm btn-ghost">Gérer</button></td></tr>'''
        for n, e, r, st, seen in members)

    audit = [
        ("Ali Kaboré", "device.reboot", "hAP-ac² · cyber-centre", "14:41", "10.66.0.12"),
        ("Mariam Traoré", "voucher.batch.create", "LOT-1104 · 300 codes", "14:20", "10.66.0.31"),
        ("Issa Ouédraogo", "device.enroll", "hEX · école-nongrémassom", "11:08", "10.66.0.44"),
        ("Système", "session.disconnect", "KAD-2287 (quota)", "13:52", "—"),
        ("Fatou Sawadogo", "plan.update", "24 heures → 3 Mbps", "09:30", "10.66.0.18"),
    ]
    arows = "".join(
        f'<tr><td class="cell-strong">{actor}</td><td class="mono small">{action}</td>'
        f'<td class="small">{obj}</td><td class="right num">{when}</td>'
        f'<td class="right mono cell-sub">{ip}</td></tr>'
        for actor, action, obj, when, ip in audit)

    content = f'''
<div class="card">
  <div class="tabs" style="padding:0 16px">
    <a class="tab active" href="#">Espace de travail</a>
    <a class="tab" href="#">Membres <span class="count">5</span></a>
    <a class="tab" href="#">Sécurité</a>
    <a class="tab" href="#">API &amp; webhooks</a>
    <a class="tab" href="#">Marque blanche</a>
    <a class="tab" href="#">Facturation</a>
  </div>
  <div class="card-body grid grid-2">
    <div class="config">
      <div class="card-title" style="margin-bottom:12px">Espace de travail</div>
      <div class="stack">
        <div class="field"><label class="label">Nom commercial</label>
          <input class="input" value="Cyber Centre-ville"></div>
        <div class="field"><label class="label">Identifiant (URL)</label>
          <div class="input-group"><span class="addon" style="border-right:0;border-left:1px solid var(--ink-200);border-radius:var(--r-md) 0 0 var(--r-md)">app.kora.bf/</span><input class="input" value="cyber-centre"></div></div>
        <div class="grid grid-2">
          <div class="field"><label class="label">Téléphone</label>
            <input class="input" value="+226 70 12 34 56"></div>
          <div class="field"><label class="label">Devise</label>
            <select class="select"><option>FCFA (XOF)</option></select></div>
        </div>
        <div class="field"><label class="label">Fuseau horaire</label>
          <select class="select"><option>Africa/Ouagadougou (GMT)</option></select></div>
        <div class="row-between"><span class="label">Envoyer les reçus par WhatsApp</span>
          <div class="switch on" role="switch" aria-checked="true"></div></div>
        <div class="row-between"><span class="label">Suspension automatique pour impayé (FAI)</span>
          <div class="switch" role="switch" aria-checked="false"></div></div>
      </div>
    </div>
    <div class="stack">
      <div class="banner banner-warn">{icon("warning", 16)}
        <div class="grow"><b>Offre Pro</b> — 7 routeurs sur 10 utilisés, 1 248 clients sur 1 500.
        <a href="#">Voir les offres</a></div></div>
      <div class="card">
        <div class="card-head"><div class="card-title">Clés d'intégration</div>
          {badge("2 actives", "badge-ok")}</div>
        <div class="list">
          <div class="list-item"><div class="li-icon ok">{icon("shield", 15)}</div>
            <div class="grow"><div class="li-title">Site vitrine</div>
              <div class="li-sub mono">sk_live_…f42a · scopes: vouchers:read, plans:read</div></div>
            <button class="btn btn-sm btn-ghost">Révoquer</button></div>
          <div class="list-item"><div class="li-icon ok">{icon("link", 15)}</div>
            <div class="grow"><div class="li-title">Caisse externe</div>
              <div class="li-sub mono">sk_live_…9c11 · scopes: payments:write</div></div>
            <button class="btn btn-sm btn-ghost">Révoquer</button></div>
          <div class="list-item"><div class="li-icon">{icon("plus", 15)}</div>
            <div class="grow"><div class="li-title">Nouvelle clé</div>
              <div class="li-sub">Le secret ne sera affiché qu'une seule fois</div></div>
            <button class="btn btn-sm btn-primary">Créer</button></div>
        </div>
      </div>
      <div class="card">
        <div class="card-head"><div class="card-title">Sécurité</div></div>
        <div class="card-body stack">
          <div class="row-between"><span class="small">Double authentification (TOTP)</span>
            {badge("Activée", "badge-ok")}</div>
          <div class="row-between"><span class="small">Dernière connexion</span>
            <span class="small mono">10.66.0.12 · il y a 2 min</span></div>
          <div class="row-between"><span class="small">Sessions ouvertes</span>
            <span class="small">2 appareils</span></div>
          <button class="btn btn-secondary btn-sm">Voir le journal d'audit</button>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="card mt-16">
  <div class="card-head"><div><div class="card-title">Membres de l'espace</div>
    <div class="card-sub">5 membres · rôles owner, admin, technicien, caissier, lecture seule</div></div>
    <button class="btn btn-sm btn-primary">{icon("users", 14)} Inviter</button></div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Membre</th><th>Rôle</th><th>Statut</th><th class="right">Dernière activité</th><th></th>
  </tr></thead><tbody>{mrows}</tbody></table></div>
</div>

<div class="card mt-16">
  <div class="card-head"><div><div class="card-title">Journal d'audit</div>
    <div class="card-sub">Immuable · conservé 24 mois · filtrable par acteur et par action</div></div>
    <div class="row"><select class="select" style="width:auto;height:30px;font-size:12.5px">
      <option>Toutes les actions</option><option>Appareils</option><option>Paiements</option>
      </select><button class="btn btn-sm btn-secondary">{icon("download", 14)} CSV</button></div></div>
  <div class="table-wrap"><table class="table"><thead><tr>
    <th>Acteur</th><th>Action</th><th>Objet</th><th class="right">Heure</th><th class="right">IP</th>
  </tr></thead><tbody>{arows}</tbody></table></div>
</div>
'''
    return shell("Équipe & réglages", "settings.html", content, crumbs=crumb("Configuration", "Équipe & réglages"),
                 page_title="Équipe et réglages",
                 page_sub="Espace de travail « Cyber Centre-ville » · offre Pro",
                 actions=f'<button class="btn btn-primary">{icon("save", 15)} Enregistrer</button>')
