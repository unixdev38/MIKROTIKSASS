#!/usr/bin/env python3
"""Génère les maquettes statiques dans design/dist/.

    python3 design/build.py
    python3 -m http.server 8000 -d design/dist
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"

sys.path.insert(0, str(ROOT))

from pages_core import dashboard, device, devices, sessions  # noqa: E402
from pages_misc import design_system, enroll, index, login, portal  # noqa: E402
from pages_sales import cashier, plans, settings, vouchers  # noqa: E402

PAGES = {
    "index.html": index,
    "login.html": login,
    "dashboard.html": dashboard,
    "devices.html": devices,
    "device.html": device,
    "enroll.html": enroll,
    "sessions.html": sessions,
    "plans.html": plans,
    "vouchers.html": vouchers,
    "cashier.html": cashier,
    "settings.html": settings,
    "portal.html": portal,
    "design-system.html": design_system,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for asset in ("styles.css", "app.js"):
        shutil.copyfile(ROOT / asset, OUT / asset)

    for name, fn in PAGES.items():
        html = fn()
        (OUT / name).write_text(html, encoding="utf-8")
        print(f"  {name:<20} {len(html) // 1024:>3} Ko")

    print(f"\n{len(PAGES)} pages générées dans {OUT}")


if __name__ == "__main__":
    main()
