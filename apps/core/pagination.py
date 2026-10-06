"""Cursor pagination for every list endpoint.

Cursor (not page-number) pagination: stable under concurrent inserts —
a new post appearing never shifts the user's page.
"""

from rest_framework.pagination import CursorPagination


class NeedyPagination(CursorPagination):
    page_size = 30
    max_page_size = 100
    page_size_query_param = "page_size"
    ordering = "-created_at"


NuvraPagination = NeedyPagination
