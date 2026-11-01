"""Export des vouchers pour l'impression et la caisse."""
from __future__ import annotations

import csv
from io import StringIO

from apps.hotspot.models import Voucher

#: Colonnes exportées (ordre stable, utilisé par l'impression et Excel).
COLUMNS = ("code", "password", "forfait", "duree", "volume_mo", "prix_fcfa", "site", "etat")


def vouchers_to_csv(vouchers: list[Voucher]) -> str:
    """Produit un CSV prêt à imprimer.

    Args:
        vouchers: Vouchers à exporter.

    Returns:
        Le contenu CSV (séparateur virgule, fins de ligne CRLF pour Excel).

    Example:
        >>> vouchers_to_csv([]).splitlines()[0]
        'code,password,forfait,duree,volume_mo,prix_fcfa,site,etat'
    """
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for voucher in vouchers:
        plan = voucher.batch.plan
        writer.writerow(
            [
                voucher.code,
                voucher.password or voucher.code,
                plan.name,
                plan.duration_label,
                plan.data_cap_mb or "illimité",
                plan.price_fcfa,
                voucher.batch.site.code,
                voucher.get_state_display(),
            ]
        )
    return buffer.getvalue()
