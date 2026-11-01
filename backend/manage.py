#!/usr/bin/env python
"""Point d'entrée Django en ligne de commande."""
import os
import sys


def main() -> None:
    """Configure l'environnement puis délègue à Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
