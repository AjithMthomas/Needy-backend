"""Consistent error envelope.

Every failure returns ``{"detail": <human message>, "code": <machine code>}``
so the Flutter client can show one thing and branch on the other.
"""

from rest_framework.views import exception_handler as drf_exception_handler


def needy_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unhandled — 500 handler takes over

    detail = response.data
    code = getattr(exc, "default_code", "error")
    if isinstance(detail, dict) and set(detail.keys()) == {"detail"}:
        detail = detail["detail"]
        if isinstance(detail, str):
            code = "invalid"
    response.data = {"detail": detail, "code": code}
    return response


nuvra_exception_handler = needy_exception_handler
