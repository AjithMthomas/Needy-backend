# nuvra Backend — Coding Standards

> **The one doc every agent and developer must read before touching `backend/`.**
> If a rule here conflicts with habit or another doc, this file wins.
> Last updated: September 29, 2026 · Stack: Django 5.2 LTS + DRF 3.16 + Postgres

---

## 0. The 30-second version

- **Layers**: `views/` (HTTP only) → `serializers` (validation) → `services.py` (business rules) → `models.py` (data). Rules live in services, never in views.
- **The client is never trusted**: moderation, gender-preference admission, capacity, karma balance, bid amounts — enforced server-side, always.
- **Every list is cursor-paginated. Every error is `{"detail", "code"}`. Every write runs the moderation screen.**
- **`make check` (ruff + pytest) must pass before any commit.** No exceptions.
- New files go exactly where §5 says. New endpoints must be added to `API_CONTRACT.md` in the same commit.

---

## 1. Project layout

```
backend/
├── manage.py               # DJANGO_SETTINGS_MODULE=config.settings.dev by default
├── requirements.txt        # runtime deps (ranged versions)
├── requirements-dev.txt    # + pytest, ruff, pre-commit
├── pyproject.toml          # ruff rules, pytest config — the tooling source of truth
├── .env.example            # copy to .env; NEVER commit .env
├── Dockerfile              # prod image (gunicorn via entrypoint.sh)
├── docker-compose.yml      # local Postgres + API
├── smoke_test.py           # end-to-end sanity run against a dev DB
├── config/                 # settings split: base/dev/test/prod + urls + asgi/wsgi
├── apps/
│   ├── core/               # base models, moderation engine, geo, pagination, errors, health/config, seed_demo
│   ├── accounts/           # Member, OTP auth, JWT, /me, badges
│   ├── posts/              # Task (all kinds), applications, saves, ratings, feed
│   ├── chat/               # ChatRoom per application, Message, since_seq polling
│   ├── auctions/           # AuctionItem, Bid (row-locked), buy-now, lazy close
│   ├── engagement/         # KarmaLedger, perks, challenges, ideas, radar
│   ├── moderation/         # reports (auto-quarantine), blocks, audit trail
│   └── notifications/      # Notification centre
└── STANDARDS.md            # ← you are here
```

---

## 2. The Golden Rules

1. **Views stay thin.** Parse input → call a service → shape the response. If a view is longer than ~40 lines or contains `if`-heavy business decisions, move it to `services.py`.
2. **One service module per app.** `apps/<app>/services.py` holds all business rules, wrapped in `@transaction.atomic` when they write.
3. **Serializers validate; services decide.** Field-level checks (types, lengths, choices) live in serializers. Cross-cutting rules (capacity, ownership, balance) live in services and raise the typed exceptions from `apps/core/exceptions.py`.
4. **Business exceptions, not generic ones.** Raise `BusinessRuleError` / `GenderRestrictedError` / `CapacityFullError` / `KarmaInsufficientError` / `ModerationBlockedError`. The handler in `apps/core/errors.py` turns them into the `{detail, code}` envelope.
5. **Never trust the client.** Re-run `apps.core.moderation.screen()` on every title/description/body write. Re-check gender admission (`Task.admits`) and capacity server-side. Never accept a computed trust value (rating, completed_count, karma) from a request body.
6. **Write-time denormalisation.** `distance_km`, `applicant_count`, `current_bid` are stored columns updated in the same transaction — reads stay index-fast. Recompute from source tables, never from client input.
7. **Optimistic locking for contended rows.** Anything money/bid/karma-shaped: `select_for_update()` inside `transaction.atomic` before validating and writing (see `auctions/services.place_bid`, `engagement/services.spend_karma`).
8. **Append-only ledgers.** Karma is an event log (`KarmaLedger`); `Member.karma` is only a cached balance. Never UPDATE or DELETE ledger rows.

---

## 3. Conventions

### Python / Django
- Python 3.11+, Django 5.2 LTS style. 100-char lines, ruff format (run `ruff format` after editing — the CI gate is `ruff check`).
- `from __future__ import annotations` on service/model modules.
- Model classes: `Task`, `Application`...; `TextChoices` for enums — **the choice values must equal the Flutter enum `.name` strings exactly** (`expensesCovered`, `femaleOnly`, `safetyCheck`).
- Time: store UTC (`USE_TZ=True`); `TIME_ZONE=Asia/Kolkata` is display-only.
- UUID primary keys everywhere (models inherit `apps.core.UUIDModel`).
- Migrations: one `makemigrations` per logical change; **never edit a migration that has been pushed**; always review the generated ops.
- No business logic in `save()` overrides or signals — put it in a service so the call site is visible.

### Names
- Modules `snake_case`; classes `PascalCase`; services are plain functions (no classes needed).
- Related names: `related_name="<plural on target>"` — e.g. `Task.creator` → `related_name="posts"`.
- Query param names in snake_case (`radius_km`, `since_seq`); JSON fields in snake_case matching the serializers.

### Serializers
- One `ModelSerializer` per projection (`TaskListSerializer` vs `TaskDetailSerializer`), not one giant serializer with conditional fields.
- Never serialize email, DOB, or safety contact outside `MemberSelfSerializer` (owner-only).
- Create-serializers validate moderation + kind-specific invariants in `validate()`; they must not call other apps' services (views do the orchestration).

### URL & versioning
- All routes live under `/api/v1/` and are registered in `apps/core/urls.py` via `include()`.
- Specific action routes (`/apply`, `/save`, `/rate`) **must be declared before** any generic `/<str:action>` catch-all.
- Actions are POST-only verbs (`/posts/{id}/start`) — no state changes on GET.

---

## 4. Testing standard (`pytest`)

- Every endpoint: a happy-path test, a forbidden/ownership test, and a validation test. Services with money/karma math get boundary tests (empty ledger, exact balance, over-balance).
- Tests run against in-memory SQLite (`config.settings.test`); no network, no free-tier coupling.
- Deterministic OTP in tests comes from `NUVRA["DEMO_MODE"]` — do not gate demo codes on `DEBUG`.
- The **smoke test** (`backend/smoke_test.py`) is the end-to-end gate: run it after any API change.
- Name tests `test_<subject>_<expectation>`; keep one behaviour per test.

```bash
# the gate
cd backend && ./.venv/Scripts/python.exe -m pytest        # 39 tests, all green
./.venv/Scripts/ruff.exe check apps config                # 0 findings
./.venv/Scripts/python.exe smoke_test.py                  # 26 checks PASS
```

---

## 5. "Where does this code go?" (agent decision table)

| I'm adding...                        | It goes in...                                      |
|--------------------------------------|----------------------------------------------------|
| A new model field                    | `apps/<app>/models.py` + migration + serializer field + `API_CONTRACT.md` row |
| A new business rule on write         | `apps/<app>/services.py` (never the view)          |
| A new error case                     | subclass in `apps/core/exceptions.py` + client code string |
| A new endpoint                       | `apps/<app>/views.py` + `urls.py` + **`API_CONTRACT.md` entry in the same commit** |
| A new vertical (like `gigs`)         | usually just `PostKind` + hub filter — do NOT add a new Task table |
| A new enum value                     | `TextChoices` here **and** Flutter `enums.dart` in the same commit, values byte-identical |
| A background job (later)             | management command in `apps/core/management/commands/` first; Celery only at Stage 3 |

---

## 6. The Scale Ladder (pre-agreed upgrade path)

Everything below is already wired to be swappable without rewrites:

| Stage | Trigger (users/day) | Change |
|-------|--------------------|--------|
| **1 — Free** (now) | 0 – ~2k | SQLite dev / Neon free Postgres, Render free web service, REST polling, console email, lazy auction close |
| **2 — Paid minimum** | ~2k – 25k | Render paid instance (no spin-down), Neon/Supabase paid Postgres, Resend SMTP (100 mails/day free tier), Play console, Cloudinary for images |
| **3 — Growth** | 25k – 200k | Redis + Celery for async (SOS fan-out, notifications), Channels/WebSockets for chat + radar (ASGI entrypoint is ready), PostGIS (`haversine_km` → native distance), read replicas |
| **4 — Scale** | 200k+ | Horizontal app replicas behind LB, dedicated search (Postgres FTS is the first step), CDN for media, partition `KarmaLedger`/`Notification` by month |

---

## 7. PR / commit checklist (Definition of Done)

- [ ] `ruff check apps config` — 0 findings
- [ ] `pytest` — all green, new logic has new tests
- [ ] `smoke_test.py` — all PASS
- [ ] New endpoints documented in `API_CONTRACT.md`
- [ ] Enum changes mirrored to `time_need_app/lib/core/models/enums.dart` (byte-identical values)
- [ ] No secrets in code or logs; `.env` not committed
- [ ] Migration reviewed (no accidental column drops)
- [ ] Root `TODO.md` + `architecture_plan.md` updated (project maintenance rule)

---

## 8. Agent-specific instructions (for AI coding agents)

1. **Read `API_CONTRACT.md` before writing any client or server route code.** The contract doc is the source of truth; do not invent endpoints silently.
2. **Never rename public API fields** (`reward_amount`, `has_checkin`...). The Flutter DTO layer (`lib/data/api/api_dto.dart`) maps them — a rename is a two-repo change.
3. **Never change `MockBackend`'s method signatures** without updating `BackendContract` (`lib/data/backend_contract.dart`) and `ApiBackend` in the same commit — the analyzer enforces parity.
4. Prefer adding a `PostKind` over a new model. The whole marketplace is one pipeline by design.
5. When adding dependencies: runtime → `requirements.txt` (ranged), dev → `requirements-dev.txt`. Justify any new runtime dep in the commit message.
6. If a change touches auth, karma, or safety rules, add the test **before** the fix and note it in `TODO.md`.
