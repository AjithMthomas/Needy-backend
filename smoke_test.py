"""Standalone end-to-end smoke test.

    .venv/Scripts/python.exe smoke_test.py

Exercises the real URL layer, serializers, auth, and services against
the dev database — the fastest full-stack confidence check.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django  # noqa: E402

django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

from apps.accounts.models import Member  # noqa: E402

FAILURES: list[str] = []
c = Client()


def show(label, response, keys=None):
    status_code = response.status_code
    try:
        body = response.json()
    except Exception:
        body = {}
    ok = 200 <= status_code < 300
    if not ok:
        FAILURES.append(f"{label}: {status_code} {body}")
    summary = {k: body[k] for k in (keys or []) if k in body}
    print(f"{'PASS' if ok else 'FAIL'} {label}: {status_code} {summary if summary else ''}")
    return body


# 0. Public endpoints
show("GET /api/v1/health", c.get("/api/v1/health"))
show("GET /api/v1/config", c.get("/api/v1/config"), ["min_app_version", "categories"])

# 1. OTP flow
show(
    "POST /auth/otp/request",
    c.post("/api/v1/auth/otp/request", {"email": "smoke@needy.app"}, content_type="application/json"),
    ["sent"],
)
from django.conf import settings  # noqa: E402

verify = show(
    "POST /auth/otp/verify",
    c.post(
        "/api/v1/auth/otp/verify",
        {"email": "smoke@needy.app", "code": settings.NUVRA["DEMO_OTP"]},
        content_type="application/json",
    ),
    ["profile_completed"],
)
auth = {"HTTP_AUTHORIZATION": f"Bearer {verify['access']}"}

# 2. Me + profile completion
show("GET /me", c.get("/api/v1/me", **auth), ["email", "karma"])
show(
    "POST /me/complete-profile",
    c.post(
        "/api/v1/me/complete-profile",
        {"name": "Smoke Tester", "gender": "other", "bio": "smoke", "categories": ["Errands"]},
        content_type="application/json",
        **auth,
    ),
    ["member"],
)

# 3. Feed + detail
feed = show("GET /posts?radius_km=5", c.get("/api/v1/posts?radius_km=5", **auth))
results = feed.get("results") or feed
task_id = results[0]["id"]
show("GET /posts/{id}", c.get(f"/api/v1/posts/{task_id}", **auth), ["title"])

# 4. Create a post
created = show(
    "POST /posts",
    c.post(
        "/api/v1/posts",
        {
            "type": "task", "kind": "regular", "title": "Smoke test post",
            "description": "Created by smoke_test.py", "category": "Errands",
            "scheduled_at": "2026-10-01T10:00:00Z", "duration_minutes": 30,
            "area": "Madiwala", "exchange": "paid", "reward_amount": 50,
            "capacity": 1, "gender_preference": "anyone",
        },
        content_type="application/json",
        **auth,
    ),
    ["title"],
)
my_task = created["id"]

# 5. Apply as another member
other = Member.objects.get(email="u5@needy.app")
Member.objects.filter(pk=other.pk).update(karma=10000)  # test budget for claims
other_auth = {"HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(other).access_token)}"}
application = show(
    f"POST /posts/{my_task}/apply",
    c.post(f"/api/v1/posts/{my_task}/apply", {"intro_message": "hi!"}, content_type="application/json", **other_auth),
    ["status"],
)

# 6. Chat room created by apply
rooms = show("GET /chat/rooms", c.get("/api/v1/chat/rooms", **auth))
room_results = rooms.get("results") or rooms
room_id = room_results[0]["id"]
show(
    f"POST /chat/rooms/{room_id}/send",
    c.post(f"/api/v1/chat/rooms/{room_id}/send", {"body": "hello from smoke"}, content_type="application/json", **other_auth),
    ["seq"],
)
show(f"GET /chat/rooms/{room_id}/messages?since_seq=0", c.get(f"/api/v1/chat/rooms/{room_id}/messages?since_seq=0", **auth))

# 7. Select applicant -> confirmed
show(
    f"POST /applications/{application['id']}/select",
    c.post(f"/api/v1/applications/{application['id']}/select", content_type="application/json", **auth),
    ["status"],
)

# 8. Auctions: upload a product photo, host one, list it live, bid as
# another member, then Buy-It-Now (self-contained — never depends on how
# old the seed data is)
png = b"\x89PNG\r\n\x1a\n" + bytes(128)
uploaded = show(
    "POST /uploads",
    c.post(
        "/api/v1/uploads",
        {"file": SimpleUploadedFile("product.png", png, content_type="image/png")},
        **auth,
    ),
    ["url"],
)
# URLValidator rejects the bare label 'testserver' (no dot); real servers
# hand out IPv4 or domain hosts, so mirror that here.
auction_image_url = uploaded["url"].replace("://testserver", "://127.0.0.1:8000")
created_auc = show(
    "POST /auctions/create",
    c.post(
        "/api/v1/auctions/create",
        {
            "title": "Smoke test auction",
            "description": "Created by smoke_test.py",
            "category": "Errands",
            "image_url": auction_image_url,
            "base_price": 100,
            "buy_it_now_price": 500,
            "duration_hours": 2,
            "area": "Madiwala",
        },
        content_type="application/json",
        **auth,
    ),
    ["title"],
)
auc_id = created_auc["id"]
auctions = show("GET /auctions?live=1", c.get("/api/v1/auctions?live=1", **auth))
auc_results = auctions.get("results") or auctions
auc = next(a for a in auc_results if a["id"] == auc_id)
show(
    f"POST /auctions/{auc_id}/bids",
    c.post(
        f"/api/v1/auctions/{auc_id}/bids",
        {"amount": float(auc["current_bid"]) + 50},
        content_type="application/json",
        **other_auth,
    ),
    ["amount"],
)
show(
    f"POST /auctions/{auc_id}/buy-now",
    c.post(f"/api/v1/auctions/{auc_id}/buy-now", content_type="application/json", **other_auth),
    ["status"],
)

# 9. Karma, perks, challenges, ideas, radar
show("GET /karma", c.get("/api/v1/karma", **auth), ["balance"])
perks = show("GET /perks", c.get("/api/v1/perks", **other_auth))  # claimer's view
perk_results = perks.get("results") or perks
unclaimed = next((p for p in perk_results if not p.get("claimed_by_me")), None)
if unclaimed is None:
    print("PASS POST /perks/{id}/claim: skipped (all vouchers already claimed)")
else:
    show(
        f"POST /perks/{unclaimed['id']}/claim",
        c.post(f"/api/v1/perks/{unclaimed['id']}/claim", content_type="application/json", **other_auth),
        ["code"],
    )
show("GET /challenges", c.get("/api/v1/challenges", **auth))
show("GET /community/ideas", c.get("/api/v1/community/ideas", **auth))
show(
    "POST /community/ideas/create",
    c.post(
        "/api/v1/community/ideas/create",
        {"title": "Smoke test idea", "details": "from smoke_test.py", "tag": "Feature"},
        content_type="application/json",
        **other_auth,
    ),
    ["upvotes"],
)
show("GET /radar", c.get("/api/v1/radar", **auth))

# 10. Notifications + moderation + toggles
show("GET /notifications", c.get("/api/v1/notifications", **auth))
show("GET /notifications/unread-count", c.get("/api/v1/notifications/unread-count", **auth))
show(
    "POST /reports",
    c.post(
        "/api/v1/reports",
        {"task_id": my_task, "reason": "spam", "details": "smoke"},
        content_type="application/json",
        **other_auth,
    ),
    ["quarantined"],
)
show("POST /me/toggle-guardian", c.post("/api/v1/me/toggle-guardian", content_type="application/json", **auth))
show("POST /me/toggle-available", c.post("/api/v1/me/toggle-available", content_type="application/json", **auth))

print()
if FAILURES:
    print(f"SMOKE FAILED — {len(FAILURES)} failure(s):")
    for failure in FAILURES:
        print("  *", failure)
    sys.exit(1)
print("SMOKE COMPLETE — all checks passed")
