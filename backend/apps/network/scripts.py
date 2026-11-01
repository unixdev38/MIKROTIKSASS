"""Génération des scripts RouterOS (enrôlement, durcissement).

Un script est un **texte** : il est produit ici, testé ici, et jamais construit à la
volée dans une vue ou un service. Les gabarits utilisent ``string.Template`` pour
éviter les erreurs de formatage liées aux accolades de RouterOS.
"""
from __future__ import annotations

from dataclasses import dataclass
from string import Template

ENROLLMENT_HEADER = "# MIKROTIK SAAS — script d'enrôlement v1 (RouterOS 7.x)"

ENROLLMENT_TEMPLATE = Template(
    """$header
# 1. Identité du routeur
/system identity set name=$identity
/system note set note="Géré par $brand — ne pas supprimer la config 'saas'"

# 2. Tunnel WireGuard sortant (fonctionne derrière CGNAT)
/interface wireguard
add name=wg-saas listen-port=51820 private-key="$wg_private" comment="saas:mgmt"
/interface wireguard peers
add interface=wg-saas public-key="$wg_peer_public" endpoint-address=$wg_endpoint \\
    endpoint-port=$wg_port allowed-address=$mgmt_network persistent-keepalive=25s \\
    comment="saas:peer"
/ip address
add address=$mgmt_ip/$mgmt_prefix interface=wg-saas comment="saas:mgmt-ip"

# 3. Utilisateur API dédié (moindre privilège)
/user group
add name=saas-api policy=api,read,write,rest-api,test comment="saas:group"
/user
add name=$api_user group=saas-api password="$api_secret" address=$mgmt_network \\
    comment="saas:api-user"

# 4. Services : on ferme tout ce qui n'est pas nécessaire
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set api disabled=yes
set api-ssl disabled=no address=$mgmt_network
set winbox address=$mgmt_network

# 5. Certificat pour api-ssl (auto-signé, épinglé côté plateforme)
/certificate
add name=saas-cert common-name=saas-api days-valid=3650 key-usage=tls-server
/ip service set api-ssl certificate=saas-cert

# 6. Heartbeat (la plateforme sait que le routeur est vivant)
/system script
add name=saas-heartbeat source={
  /tool fetch url="$heartbeat_url" http-method=post \\
    http-header-field="X-Device-Token:$heartbeat_token" \\
    http-data="{\\"ver\\":\\"" . [/system resource get version] . "\\"}" keep-result=no
}
/system scheduler
add name=saas-heartbeat interval=1m on-event=saas-heartbeat comment="saas:heartbeat"
"""
)


@dataclass(frozen=True, slots=True)
class EnrollmentScriptContext:
    """Données nécessaires au rendu d'un script d'enrôlement.

    Attributes:
        identity: Nom RouterOS à appliquer (site + routeur).
        device_name: Nom du routeur.
        site_name: Nom du site.
        management_ip: Adresse IP dans le tunnel.
        management_network: Réseau autorisé (``10.66.0.0/24``).
        management_prefix: Longueur de préfixe du tunnel (24).
        wireguard_private_key: Clé privée générée pour le routeur.
        wireguard_peer_public_key: Clé publique du concentrateur.
        wireguard_endpoint: Hôte du concentrateur.
        wireguard_port: Port d'écoute du concentrateur.
        api_username: Utilisateur API à créer.
        api_secret: Mot de passe de cet utilisateur.
        heartbeat_url: URL appelée chaque minute.
        heartbeat_token: Jeton d'authentification du heartbeat.
        brand: Nom de marque affiché sur le routeur.
    """

    identity: str
    device_name: str
    site_name: str
    management_ip: str
    management_network: str
    management_prefix: int
    wireguard_private_key: str
    wireguard_peer_public_key: str
    wireguard_endpoint: str
    wireguard_port: int
    api_username: str
    api_secret: str
    heartbeat_url: str
    heartbeat_token: str
    brand: str = "Kora"


def render_enrollment_script(context: EnrollmentScriptContext) -> str:
    """Rend le script RouterOS d'enrôlement.

    Args:
        context: Valeurs à injecter (secrets inclus).

    Returns:
        Le script complet, prêt à être collé dans le terminal WinBox.

    Example:
        >>> ctx = EnrollmentScriptContext(...)  # voir tests/test_device_enrollment.py
        >>> script = render_enrollment_script(ctx)
        >>> script.startswith("# MIKROTIK SAAS")
        True
    """
    return ENROLLMENT_TEMPLATE.substitute(
        header=ENROLLMENT_HEADER,
        identity=_quote_routeros(context.identity),
        device_name=context.device_name,
        site_name=context.site_name,
        mgmt_ip=context.management_ip,
        mgmt_network=context.management_network,
        mgmt_prefix=context.management_prefix,
        wg_private=context.wireguard_private_key,
        wg_peer_public=context.wireguard_peer_public_key,
        wg_endpoint=context.wireguard_endpoint,
        wg_port=context.wireguard_port,
        api_user=context.api_username,
        api_secret=context.api_secret,
        heartbeat_url=context.heartbeat_url,
        heartbeat_token=context.heartbeat_token,
        brand=context.brand,
    )


def _quote_routeros(value: str) -> str:
    """Met une valeur entre guillemets RouterOS en échappant les guillemets internes.

    Args:
        value: Chaîne à échapper.

    Returns:
        La valeur entourée de guillemets, prête pour RouterOS.
    """
    safe = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{safe}"'
