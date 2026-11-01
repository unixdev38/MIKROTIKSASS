"""Écrans autonomes : connexion, enrôlement, portail captif, design system, couverture."""
from kit import (badge, crumb, icon, qr_svg, shell, standalone, status_badge)


def login() -> str:
    body = f'''
<div class="auth">
  <aside class="auth-aside">
    <div class="row">
      <div class="brand-mark">K</div>
      <div><div class="brand-name">Kora</div><div class="brand-sub">Cybers &amp; FAI</div></div>
    </div>

    <div>
      <div class="quote">Votre réseau Wi-Fi, <em>sous contrôle</em> — même quand vous n'êtes pas sur place.</div>
      <div class="auth-points">
        <div class="auth-point"><span class="tick">{icon("check", 16)}</span>
          Vouchers imprimés ou envoyés par WhatsApp, coupure automatique en fin de forfait.</div>
        <div class="auth-point"><span class="tick">{icon("check", 16)}</span>
          Vos routeurs MikroTik sont joints par un tunnel privé : aucun port exposé sur Internet.</div>
        <div class="auth-point"><span class="tick">{icon("check", 16)}</span>
          Orange Money, Moov Money, Wave : l'argent arrive et la session s'ouvre toute seule.</div>
      </div>
    </div>

    <div class="small" style="color:#7f938e">
      Maquette de démonstration · aucune donnée réelle · <a href="index.html" style="color:#9fd8c8">toutes les maquettes</a>
    </div>
  </aside>

  <main class="auth-main">
    <div class="auth-form">
      <h1>Connexion</h1>
      <p class="sub">Accédez à votre espace de travail.</p>
      <div class="stack">
        <div class="field"><label class="label" for="email">Adresse e-mail</label>
          <input class="input" id="email" type="email" value="ali@cybercentre.bf" autocomplete="username"></div>
        <div class="field"><label class="label" for="pwd">Mot de passe</label>
          <input class="input" id="pwd" type="password" value="motdepasse" autocomplete="current-password">
          <div class="row-between"><label class="row small muted"><input type="checkbox" checked> Se souvenir de moi</label>
            <a class="small" href="#">Mot de passe oublié ?</a></div></div>
        <button class="btn btn-primary btn-block btn-lg">Se connecter</button>
      </div>
      <div class="sep">ou</div>
      <button class="btn btn-secondary btn-block">Continuer avec Google</button>
      <div class="demo-hint">Prototype : cliquez sur « Se connecter » puis utilisez le menu de gauche.
        En production, la double authentification est obligatoire pour les comptes administrateurs.</div>
      <p class="small muted center mt-16">Pas encore de compte ? <a href="#">Créer un espace (essai 14 jours)</a></p>
    </div>
  </main>
</div>
'''
    return standalone("Connexion", body)


def enroll() -> str:
    script = '''<span class="c-comment"># MIKROTIK SAAS — script d'enrôlement v1 (RouterOS 7.x)</span>
<span class="c-comment"># 1. Identité</span>
<span class="c-cmd">/system identity set</span> name=<span class="c-var">"cyber-centre-hap01"</span>
<span class="c-cmd">/system note set</span> note=<span class="c-var">"Géré par Kora — ne pas supprimer la config 'saas'"</span>

<span class="c-comment"># 2. Tunnel sortant (fonctionne derrière CGNAT)</span>
<span class="c-cmd">/interface wireguard add</span> name=wg-saas listen-port=51820 \\
  private-key=<span class="c-var">"aB3k…9fQ"</span> comment=<span class="c-var">"saas:mgmt"</span>
<span class="c-cmd">/interface wireguard peers add</span> interface=wg-saas \\
  public-key=<span class="c-var">"hZ8p…2Lc"</span> endpoint-address=<span class="c-var">vpn.kora.bf</span> \\
  endpoint-port=51820 allowed-address=10.66.0.0/24 persistent-keepalive=25s
<span class="c-cmd">/ip address add</span> address=10.66.1.14/24 interface=wg-saas

<span class="c-comment"># 3. Utilisateur API dédié (moindre privilège)</span>
<span class="c-cmd">/user group add</span> name=saas-api policy=api,read,write,rest-api,test
<span class="c-cmd">/user add</span> name=saas-api group=saas-api password=<span class="c-var">"…24 caractères…"</span> \\
  address=10.66.0.0/24

<span class="c-comment"># 4. Services : on ferme tout ce qui n'est pas nécessaire</span>
<span class="c-cmd">/ip service set</span> telnet disabled=yes; <span class="c-cmd">/ip service set</span> ftp disabled=yes
<span class="c-cmd">/ip service set</span> www disabled=yes; <span class="c-cmd">/ip service set</span> api disabled=yes
<span class="c-cmd">/ip service set</span> api-ssl disabled=no address=10.66.0.0/24
<span class="c-cmd">/ip service set</span> winbox address=10.66.0.0/24

<span class="c-comment"># 5. Heartbeat (la plateforme sait que le routeur est vivant)</span>
<span class="c-cmd">/system scheduler add</span> name=saas-heartbeat interval=1m on-event=saas-heartbeat'''

    content = f'''
<div class="stepper">
  <div class="step done"><div class="step-num">{icon("check", 13)}</div><div class="step-label">Site</div></div>
  <div class="step-line"></div>
  <div class="step done"><div class="step-num">{icon("check", 13)}</div><div class="step-label">Modèle</div></div>
  <div class="step-line"></div>
  <div class="step current"><div class="step-num">3</div><div class="step-label">Script</div></div>
  <div class="step-line"></div>
  <div class="step"><div class="step-num">4</div><div class="step-label">Connexion</div></div>
</div>

<div class="grid grid-main">
  <div class="stack">
    <div class="card">
      <div class="card-head"><div><div class="card-title">1 · Copiez ce script dans le routeur</div>
        <div class="card-sub">WinBox → New Terminal, ou WebFig → Terminal. Collez, puis Entrée.</div></div>
        {badge("À usage unique", "badge-warn")}</div>
      <div class="card-body">
        <div class="banner banner-warn" style="margin-bottom:12px">{icon("warning", 16)}
          <div class="grow">Ce script crée un tunnel et un utilisateur API restreint. Il <b>ne modifie pas</b>
          votre configuration hotspot existante.</div></div>
        <div class="code-block">{script}
          <button class="code-copy" type="button">Copier</button></div>
        <div class="row mt-16 wrap">
          <button class="btn btn-secondary">{icon("download", 15)} Télécharger .rsc</button>
          <button class="btn btn-secondary">{icon("external", 15)} Ouvrir le guide</button>
          <span class="hint grow">Script valable 24 h · régénérable à tout moment.</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-head"><div class="card-title">2 · Vérifications avant de commencer</div></div>
      <div class="list">
        <div class="list-item"><div class="li-icon ok">{icon("check", 15)}</div>
          <div class="grow"><div class="li-title">RouterOS 7.1 ou supérieur</div>
          <div class="li-sub">Détecté : 7.16.2 · compatible REST et WireGuard</div></div></div>
        <div class="list-item"><div class="li-icon ok">{icon("check", 15)}</div>
          <div class="grow"><div class="li-title">Horloge synchronisée</div>
          <div class="li-sub">Requis pour TLS et RADIUS</div></div></div>
        <div class="list-item"><div class="li-icon warn">{icon("warning", 15)}</div>
          <div class="grow"><div class="li-title">Pare-feu : sortie UDP 51820 autorisée</div>
          <div class="li-sub">Si bloqué, le routeur restera en « en attente »</div></div></div>
        <div class="list-item"><div class="li-icon">{icon("clock", 15)}</div>
          <div class="grow"><div class="li-title">Compte administrateur disponible</div>
          <div class="li-sub">Nécessaire pour coller le script (une seule fois)</div></div></div>
      </div>
    </div>
  </div>

  <div class="stack">
    <div class="card">
      <div class="card-head"><div class="card-title">3 · Connexion du routeur</div></div>
      <div class="card-body" style="text-align:center">
        <div style="padding:6px 0">{qr_svg("enroll-cc-hap-01", 132)}</div>
        <div class="small muted">Scannez pour ouvrir le script sur un téléphone</div>
        <div class="row center mt-16" data-demo="enroll-wait" style="justify-content:center;flex-wrap:wrap">
          <span class="badge badge-info"><span class="dot"></span>En attente de connexion…</span>
          <span class="muted small">tunnel WireGuard</span>
          <button class="btn btn-sm btn-secondary">{icon("refresh", 13)} Rafraîchir</button>
        </div>
        <div class="hint mt-8" id="wait">La détection prend généralement moins de 30 secondes.</div>
      </div>
    </div>

    <div class="card">
      <div class="card-head"><div class="card-title">Récapitulatif</div></div>
      <div class="card-body stack">
        <div class="row-between"><span class="muted small">Site</span><span class="strong">Cyber Centre-ville</span></div>
        <div class="row-between"><span class="muted small">Modèle</span><span class="strong">hAP ac² (RB2011)</span></div>
        <div class="row-between"><span class="muted small">Adresse de management</span><span class="mono">10.66.1.14</span></div>
        <div class="row-between"><span class="muted small">Transport</span><span class="strong">WireGuard + REST</span></div>
        <div class="row-between"><span class="muted small">Repli</span><span class="strong">API binaire (8729)</span></div>
      </div>
    </div>

    <div class="banner banner-brand">{icon("shield", 16)}
      <div class="grow">Aucun port de management ne sera ouvert vers Internet : le routeur initie lui-même
      le tunnel. <a href="devices.html">Retour au parc</a>.</div></div>
  </div>
</div>

<div class="card mt-16">
  <div class="card-head"><div class="card-title">Si la connexion ne s'établit pas</div></div>
  <div class="grid grid-3" style="padding:0 16px 16px">
    <div class="stack" style="gap:4px"><div class="strong small">1. Le script a-t-il été collé en entier ?</div>
      <div class="hint">WinBox tronque parfois le collage : vérifiez que l'interface <span class="mono">wg-saas</span> existe.</div></div>
    <div class="stack" style="gap:4px"><div class="strong small">2. La sortie UDP 51820 est-elle autorisée ?</div>
      <div class="hint">Testez depuis le routeur : <span class="mono">/tool fetch url="https://vpn.kora.bf"</span>.</div></div>
    <div class="stack" style="gap:4px"><div class="strong small">3. L'horloge est-elle à l'heure ?</div>
      <div class="hint">Un décalage de plus de 5 minutes invalide TLS.</div></div>
  </div>
</div>
'''
    return shell("Enrôlement", "devices.html", content,
                 crumbs=f'<span>Réseau</span> {icon("arrow", 12)} <a href="devices.html">Routeurs</a> {icon("arrow", 12)} <b>Enrôlement</b>',
                 page_title="Ajouter un routeur",
                 page_sub="Étape 3 sur 4 · connexion sécurisée par tunnel")


def portal() -> str:
    plans = [("24 heures", "3 Mbps · 2 Go", "500", True), ("1 heure", "2 Mbps · illimité", "200", False),
             ("7 jours", "5 Mbps · 15 Go", "2 000", False)]

    def plan_html(items):
        return "".join(
            f'''<div class="plan-option{' selected' if sel else ''}">
              <div class="p-main"><div class="p-name">{n}</div><div class="p-meta">{meta}</div></div>
              <div class="p-price">{p} F</div></div>'''
            for n, meta, p, sel in items)

    body = f'''
<div class="phone-stage">
  <div>
    <div class="badge badge-brand" style="margin-bottom:10px">Étape 1 · achat</div>
    <div class="phone">
      <div class="phone-screen">
        <div class="phone-notch"><span></span></div>
        <div class="portal-hero">
          <div class="portal-brand"><div class="mark">C</div> Cyber Centre-ville</div>
          <h2>Bienvenue 👋</h2>
          <p>Choisissez une offre pour vous connecter.</p>
        </div>
        <div class="portal-body">
          {plan_html(plans)}
          <div class="label" style="margin-top:2px">Payer avec</div>
          <div class="pay-methods">
            <div class="pay-method selected"><div class="pm-logo pm-orange">Orange</div>
              <div class="pm-name">Orange Money</div></div>
            <div class="pay-method"><div class="pm-logo pm-moov">Moov</div>
              <div class="pm-name">Moov Money</div></div>
            <div class="pay-method"><div class="pm-logo pm-wave">Wave</div>
              <div class="pm-name">Wave</div></div>
          </div>
          <div class="field"><label class="label">Numéro de téléphone</label>
            <input class="input" value="70 12 34 56"></div>
          <button class="btn btn-primary btn-block btn-lg">Payer 500 FCFA</button>
          <div class="hint center">Vous recevrez une demande de confirmation sur votre téléphone.</div>
          <div class="sep">ou</div>
          <button class="btn btn-secondary btn-block">J'ai déjà un code</button>
        </div>
        <div class="portal-foot">Mentions légales · Aide · propulsé par Kora</div>
      </div>
    </div>
  </div>

  <div>
    <div class="badge badge-brand" style="margin-bottom:10px">Étape 2 · accès</div>
    <div class="phone">
      <div class="phone-screen">
        <div class="phone-notch"><span></span></div>
        <div class="portal-hero">
          <div class="portal-brand"><div class="mark">C</div> Cyber Centre-ville</div>
          <h2>Vous êtes connecté ✅</h2>
          <p>Votre code est actif pendant 24 heures.</p>
        </div>
        <div class="portal-body">
          <div class="ticket">
            <div class="small muted">Votre code d'accès</div>
            <div class="code">KAD-7734</div>
            {qr_svg("KAD-7734", 100)}
            <div class="small" style="margin-top:8px">24 heures · 3 Mbps · 2 Go</div>
          </div>
          <div class="row-between"><span class="muted small">Temps restant</span>
            <span class="strong num">23 h 41 min</span></div>
          <div class="row-between"><span class="muted small">Données consommées</span>
            <span class="strong num">96 Mo / 2 Go</span></div>
          <div class="row-between"><span class="muted small">Débit</span>
            <span class="strong">3 Mbps</span></div>
          <button class="btn btn-primary btn-block">Partager le code par WhatsApp</button>
          <button class="btn btn-secondary btn-block">Prolonger</button>
        </div>
        <div class="portal-foot">Paiement Orange Money · reçu #P-88412</div>
      </div>
    </div>
  </div>
</div>

<div style="position:fixed;left:16px;bottom:16px">
  <a class="btn btn-secondary btn-sm" href="index.html">{icon("arrow", 14)} Toutes les maquettes</a>
</div>
'''
    return standalone("Portail captif", body)


def design_system() -> str:
    swatches = [
        ("--brand-600", "#0e876f", "Brand 600"), ("--brand-500", "#0fa37f", "Brand 500"),
        ("--brand-100", "#d8f3ea", "Brand 100"), ("--accent-500", "#f2a93b", "Accent"),
        ("--ink-900", "#0b1220", "Ink 900"), ("--ink-500", "#5b6b82", "Ink 500"),
        ("--ink-200", "#dde3ec", "Ink 200"), ("--ink-50", "#f6f8fb", "Ink 50"),
        ("--ok-600", "#0f9d58", "Succès"), ("--warn-600", "#b26a00", "Alerte"),
        ("--danger-600", "#d13636", "Erreur"), ("--info-600", "#1f6feb", "Info"),
    ]
    sw = "".join(
        f'<div class="swatch"><div class="chip" style="background:{hexv}"></div>'
        f'<div class="meta"><b>{name}</b>{var}</div></div>' for var, hexv, name in swatches)

    icons = ["grid", "router", "activity", "bell", "tag", "ticket", "wallet", "users", "gear",
             "cash", "wifi", "shield", "terminal", "download", "refresh", "check", "warning", "power"]
    ic = "".join(f'<div class="icon-btn">{icon(n, 17)}</div>' for n in icons)

    content = f'''
<div class="grid grid-2">
  <div class="card">
    <div class="card-head"><div><div class="card-title">Couleurs</div>
      <div class="card-sub">Tout est piloté par des variables CSS : la marque blanche ne change que ce bloc</div></div></div>
    <div class="card-body"><div class="ds-swatches">{sw}</div></div>
  </div>

  <div class="card">
    <div class="card-head"><div><div class="card-title">Typographie</div>
      <div class="card-sub">Police système : aucun téléchargement, rendu immédiat en 3G</div></div></div>
    <div class="card-body stack">
      <div style="font-size:26px;font-weight:700;letter-spacing:-.8px">Titre de page · 22–26 px</div>
      <div style="font-size:17px;font-weight:650">Titre de section · 17 px</div>
      <div style="font-size:14px;font-weight:600">Titre de carte · 14 px / 650</div>
      <div style="font-size:13.5px">Corps de texte · 13,5 px · interligne 1,45</div>
      <div class="muted small">Légende · 12 px · couleur Ink 500</div>
      <div class="mono">Donnée technique · monospace 12,5 px</div>
      <div class="num strong" style="font-size:22px">84 500 FCFA <span class="muted small">chiffres tabulaires</span></div>
    </div>
  </div>
</div>

<div class="grid grid-2 mt-16">
  <div class="card">
    <div class="card-head"><div class="card-title">Boutons</div></div>
    <div class="card-body stack">
      <div class="ds-row">
        <button class="btn btn-primary">{icon("cash", 15)} Action principale</button>
        <button class="btn btn-secondary">Action secondaire</button>
        <button class="btn btn-ghost">Discrète</button>
        <button class="btn btn-danger">Danger</button>
        <button class="btn btn-danger-soft">Danger doux</button>
      </div>
      <div class="ds-row">
        <button class="btn btn-primary btn-sm">Petit</button>
        <button class="btn btn-primary">Normal</button>
        <button class="btn btn-primary btn-lg">Grand</button>
        <button class="btn btn-primary" disabled>Désactivé</button>
      </div>
      <div class="ds-row">
        <button class="icon-btn" aria-label="Exemple">{icon("bell", 16)}</button>
        <button class="icon-btn" aria-label="Exemple">{icon("refresh", 16)}</button>
        <div class="switch on"></div><div class="switch"></div>
      </div>
      <div class="hint">Un seul bouton primaire par écran. Les actions destructrices sont en rouge et
      demandent confirmation.</div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><div class="card-title">Badges et statuts</div></div>
    <div class="card-body stack">
      <div class="ds-row">{status_badge("En ligne")} {status_badge("Dégradé")} {status_badge("Hors ligne")}
        {status_badge("En attente")} {badge("Connecté", "badge-live", True)}</div>
      <div class="ds-row">{status_badge("Actif")} {status_badge("Partiel")} {status_badge("Payé")}
        {status_badge("Impayé")} {badge("Nouveau", "badge-brand")}</div>
      <div class="divider" style="height:1px;background:var(--ink-100)"></div>
      <div class="ds-row"><span class="badge badge-danger"><span class="dot"></span>2 alertes</span>
        <span class="badge">Neutre</span></div>
      <div class="hint">Un statut n'est jamais signalé par la couleur seule : point + texte (daltonisme).</div>
    </div>
  </div>
</div>

<div class="grid grid-2 mt-16">
  <div class="card">
    <div class="card-head"><div class="card-title">Champs et formulaires</div></div>
    <div class="card-body stack">
      <div class="field"><label class="label">Nom du site</label>
        <input class="input" value="Cyber Centre-ville">
        <span class="hint">Apparaîtra sur les reçus et les coupons.</span></div>
      <div class="field"><label class="label">Débit (Mbps)</label>
        <div class="input-group"><input class="input" value="-3" style="border-color:var(--danger-600)">
          <span class="addon">Mbps</span></div>
        <span class="error-text">La valeur doit être supérieure à 0.</span></div>
      <div class="field"><label class="label">Routeur</label>
        <select class="select"><option>hAP-ac² · cyber-centre</option></select></div>
      <div class="row-between"><span class="label">Achetable en ligne</span><div class="switch on"></div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><div class="card-title">Tableau de données</div>
      <span class="muted small">En-têtes 11 px, lignes 13 px</span></div>
    <div class="card-body tight"><div class="table-wrap"><table class="table compact"><thead><tr>
      <th>Routeur</th><th>Statut</th><th class="right">Clients</th></tr></thead><tbody>
      <tr><td class="cell-strong">hAP-ac² · cyber-centre</td><td>{status_badge("En ligne")}</td>
        <td class="right num">18</td></tr>
      <tr><td class="cell-strong">hAP-lite · ouaga2000</td><td>{status_badge("Dégradé")}</td>
        <td class="right num">9</td></tr>
      <tr><td class="cell-strong">CHR · hôtel</td><td>{status_badge("Hors ligne")}</td>
        <td class="right num">0</td></tr>
    </tbody></table></div></div>
    <div class="card-body">
      <div class="row-between" style="border-top:1px solid var(--ink-100);padding-top:12px">
        <span class="muted small">1–3 sur 11</span>
        <div class="row"><button class="btn btn-sm btn-secondary">Précédent</button>
          <button class="btn btn-sm btn-secondary">Suivant</button></div>
      </div>
    </div>
  </div>
</div>

<div class="grid grid-3 mt-16">
  <div class="card"><div class="card-head"><div class="card-title">Retour utilisateur</div></div>
    <div class="card-body stack">
      <div class="toast"><span class="t-ic">{icon("check", 17)}</span>
        <div><b>Lot généré</b><div class="small" style="color:#a9b8cc">100 vouchers prêts à imprimer.</div></div></div>
      <div class="banner banner-warn">{icon("warning", 15)}<div class="grow">Disque à 91 %.</div></div>
      <div class="banner banner-danger">{icon("power", 15)}<div class="grow">Routeur injoignable.</div></div>
    </div>
  </div>

  <div class="card"><div class="card-head"><div class="card-title">Modale de confirmation</div></div>
    <div class="card-body">
      <div class="modal-card">
        <div class="modal-body">
          <div class="row"><div class="li-icon danger">{icon("power", 16)}</div>
            <div><div class="strong">Redémarrer ce routeur ?</div>
            <div class="muted small">Les 18 clients connectés seront déconnectés environ 90 secondes.</div></div></div>
          <div class="field mt-16"><label class="label">Tapez « cyber-centre » pour confirmer</label>
            <input class="input" placeholder="cyber-centre"></div>
        </div>
        <div class="modal-foot"><button class="btn btn-secondary btn-sm">Annuler</button>
          <button class="btn btn-danger btn-sm">Redémarrer</button></div>
      </div>
    </div>
  </div>

  <div class="card"><div class="card-head"><div class="card-title">États vides et chargement</div></div>
    <div class="card-body stack">
      <div class="empty" style="padding:10px">
        <div class="empty-ic">{icon("router", 20)}</div>
        <h4>Aucun routeur</h4>
        <p>Ajoutez votre premier routeur pour commencer.</p>
        <button class="btn btn-sm btn-primary">Ajouter un routeur</button>
      </div>
      <div class="stack" style="gap:8px">
        <div class="skeleton" style="width:70%"></div>
        <div class="skeleton" style="width:90%"></div>
        <div class="skeleton" style="width:50%"></div>
      </div>
    </div>
  </div>
</div>

<div class="card mt-16">
  <div class="card-head"><div><div class="card-title">Iconographie</div>
    <div class="card-sub">Trait 1,7 px, 24×24, une seule famille — pas d'emoji dans l'interface métier</div></div>
    <a class="btn btn-sm btn-secondary" href="index.html">{icon("arrow", 14)} Maquettes</a></div>
  <div class="card-body"><div class="ds-row">{ic}</div></div>
</div>
'''
    return shell("Design system", "design-system.html", content,
                 crumbs=crumb("Prototype", "Design system"),
                 page_title="Design system",
                 page_sub="Jetons, composants et règles — la base à transmettre aux développeurs")


def index() -> str:
    screens = [
        ("Tableau de bord", "dashboard.html", "Pilotage",
         "Recette du jour, sessions, état du parc, alertes, encaissements récents.", "kpi"),
        ("Parc de routeurs", "devices.html", "Pilotage",
         "Inventaire filtrable, statut, version RouterOS, dernier contact.", "table"),
        ("Fiche routeur", "device.html", "Pilotage",
         "Santé, interfaces, trafic, événements, actions de maintenance.", "detail"),
        ("Sessions actives", "sessions.html", "Pilotage",
         "Temps réel, consommation, déconnexion forcée (CoA puis API).", "table"),
        ("Forfaits", "plans.html", "Vente",
         "Offres, prix FCFA, quotas, profils hotspot synchronisés.", "grid"),
        ("Vouchers", "vouchers.html", "Vente",
         "Génération de lots, aperçu du coupon, QR, imports/exports.", "grid"),
        ("Caisse", "cashier.html", "Vente",
         "Vente en 3 clics, journal du jour, reçu et envoi WhatsApp.", "form"),
        ("Équipe & réglages", "settings.html", "Configuration",
         "Membres et rôles, clés API, sécurité, journal d'audit.", "form"),
        ("Enrôlement d'un routeur", "enroll.html", "Parcours",
         "Assistant en 4 étapes, script prêt à coller, attente de connexion.", "form"),
        ("Connexion", "login.html", "Parcours",
         "Écran d'entrée, promesse produit, double authentification.", "auth"),
        ("Portail captif", "portal.html", "Client final",
         "Achat mobile money et page de confirmation, en mobile.", "phone"),
        ("Design system", "design-system.html", "Référence",
         "Couleurs, typographie, composants, états, modale, iconographie.", "grid"),
    ]

    def thumb(kind: str) -> str:
        if kind == "table":
            return ('<div class="mini"><div class="mini-bar w50"></div>'
                    '<div class="mini-bar brand w70"></div><div class="mini-bar"></div>'
                    '<div class="mini-bar"></div><div class="mini-bar w70"></div></div>')
        if kind == "kpi":
            return ('<div class="mini"><div class="mini-bar w30"></div>'
                    '<div class="mini-cols"><div class="mini-col"></div><div class="mini-col"></div>'
                    '<div class="mini-col"></div><div class="mini-col"></div></div>'
                    '<div class="mini-bar w50"></div></div>')
        if kind == "detail":
            return ('<div class="mini"><div class="mini-bar w50"></div>'
                    '<div class="mini-cols"><div class="mini-col" style="flex:2"></div>'
                    '<div class="mini-col"></div></div><div class="mini-bar w70"></div></div>')
        if kind == "auth":
            return ('<div class="mini"><div class="mini-cols"><div class="mini-col" '
                    'style="background:#0b1220;border-color:#0b1220"></div><div class="mini-col"></div></div></div>')
        if kind == "phone":
            return ('<div class="mini" style="align-items:center">'
                    '<div style="width:46px;height:80px;border-radius:8px;background:var(--brand-700)"></div>'
                    '<div class="mini-bar w50"></div></div>')
        if kind == "form":
            return ('<div class="mini"><div class="mini-bar w30"></div><div class="mini-bar brand"></div>'
                    '<div class="mini-bar"></div><div class="mini-bar w70"></div></div>')
        return ('<div class="mini"><div class="mini-cols"><div class="mini-col"></div>'
                '<div class="mini-col"></div><div class="mini-col"></div></div>'
                '<div class="mini-cols"><div class="mini-col"></div><div class="mini-col"></div>'
                '<div class="mini-col"></div></div></div>')

    cards = "".join(
        f'''<a class="screen-card" href="{href}">
          <div class="screen-thumb">{thumb(kind)}</div>
          <div class="screen-meta"><span class="tag">{cat}</span><h3>{name}</h3><p>{desc}</p></div>
        </a>''' for name, href, cat, desc, kind in screens)

    body = f'''
<div class="cover">
  <div class="cover-hero">
    <div>
      <div class="row" style="margin-bottom:14px">
        <div class="brand-mark" style="width:34px;height:34px">K</div>
        <div><div class="brand-name" style="color:var(--ink-900)">Kora</div>
          <div class="brand-sub" style="color:var(--ink-400)">Maquettes · prototype statique</div></div>
      </div>
      <h1>Le réseau, sous contrôle.</h1>
      <p class="lead">Maquettes haute fidélité de la console de gestion et du portail captif :
        hotspot Wi-Fi, vouchers, caisse, supervision du parc MikroTik. Navigation cliquable,
        aucune dépendance externe, tout tient en HTML/CSS.</p>
      <div class="row mt-16 wrap">
        <a class="btn btn-primary" href="dashboard.html">{icon("grid", 15)} Ouvrir la console</a>
        <a class="btn btn-secondary" href="portal.html">{icon("wifi", 15)} Voir le portail captif</a>
        <a class="btn btn-secondary" href="design-system.html">{icon("shield", 15)} Design system</a>
      </div>
    </div>
    <div class="note" style="max-width:300px">
      <b>Prototype, pas production.</b> Les données sont fictives, les QR codes ne sont pas scannables
      et aucune action n'appelle de serveur. Les règles réelles sont dans <span class="mono">docs/</span>.
    </div>
  </div>

  <div class="screen-grid">{cards}</div>

  <div class="grid grid-3 mt-24">
    <div class="note"><b>Marque de travail.</b> « Kora » est un nom provisoire. Toute l'identité tient
      dans les variables CSS de <span class="mono">styles.css</span>.</div>
    <div class="note"><b>Pensé 3G.</b> Aucune police distante, aucun CDN, JS minimal : la console s'ouvre
      même sur une connexion instable.</div>
    <div class="note"><b>Prêt à traduire.</b> Tous les libellés sont en français, les montants en FCFA
      avec des chiffres tabulaires.</div>
  </div>

  <p class="muted small mt-24">Généré par <span class="mono">design/build.py</span> —
    régénérer avec <span class="mono">python3 design/build.py</span>.</p>
</div>
'''
    return standalone("Maquettes", body)
