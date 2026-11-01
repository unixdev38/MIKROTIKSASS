"""Pagination standard de l'API."""
from __future__ import annotations

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Pagination par numéro de page, bornée.

    Attributes:
        page_size: Éléments par défaut.
        max_page_size: Plafond pour éviter les extractions massives.
        page_size_query_param: Paramètre de surcharge (``?page_size=``).
    """

    page_size = 50
    max_page_size = 200
    page_size_query_param = "page_size"
