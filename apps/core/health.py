"""Health + client config endpoints.

/health  — liveness for Render/uptime monitors (checks DB).
/config  — client bootstrap: categories, enums, service fee, kill switch.
           Lets the app adapt without a store release (min_version gate,
           maintenance mode, moderation copy).
"""

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import moderation

CATEGORY_NAMES = [
    "Errands",
    "Company",
    "Food",
    "Sports",
    "Study",
    "Culture",
    "Transport",
]


def _db_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except (OperationalError, ProgrammingError):
        return False


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ok = _db_ok()
        return Response(
            {"status": "ok" if ok else "degraded", "database": ok},
            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ConfigView(APIView):
    """Bootstrap payload — the app calls this once on cold start."""

    permission_classes = [AllowAny]

    def get(self, request):
        nuvra = settings.NUVRA
        return Response(
            {
                "min_app_version": "0.1.0",
                "maintenance_mode": False,
                "service_fee_percent": nuvra["SERVICE_FEE_PERCENT"],
                "categories": CATEGORY_NAMES,
                "enums": {
                    "post_type": ["task", "company", "offer"],
                    "post_kind": [
                        "regular",
                        "emergency",
                        "gig",
                        "room",
                        "team",
                        "trip",
                    ],
                    "exchange_mode": [
                        "paid",
                        "free",
                        "treat",
                        "expensesCovered",
                        "negotiable",
                        "barter",
                    ],
                    "gender_preference": ["anyone", "femaleOnly", "maleOnly"],
                    "task_risk": ["low", "medium", "high"],
                    "task_status": [
                        "draft",
                        "safetyCheck",
                        "published",
                        "confirmed",
                        "active",
                        "completed",
                        "cancelled",
                        "expired",
                        "disputed",
                    ],
                    "application_status": [
                        "interested",
                        "chatting",
                        "selected",
                        "declined",
                        "withdrawn",
                    ],
                    "trust_badge": [
                        "punctual",
                        "friendly",
                        "safeHelper",
                        "verifiedScout",
                    ],
                    "auction_status": [
                        "active",
                        "endingSoon",
                        "completed",
                        "cancelled",
                    ],
                },
                "moderation": {
                    "hard_reason": moderation.HARD_REASON,
                    "soft_reason": moderation.SOFT_REASON,
                },
            }
        )
