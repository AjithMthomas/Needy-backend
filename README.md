# needy Backend (Stage 2)

Django 5.2 LTS + Django REST Framework API for the needy hyperlocal
micro-marketplace. Designed for **one developer**: batteries included,
free-tier deployable, and a pre-agreed scale ladder (see
[STANDARDS.md §6](STANDARDS.md)).

**Read [STANDARDS.md](STANDARDS.md) before writing code.**
**Read [API_CONTRACT.md](API_CONTRACT.md) before touching routes or the Flutter DTO layer.**

## Quickstart (zero cost, 3 minutes)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # Windows Git Bash
# source .venv/bin/activate && pip install -r requirements-dev.txt  # macOS/Linux

./.venv/Scripts/python.exe manage.py migrate
./.venv/Scripts/python.exe manage.py seed_demo        # full Madiwala demo world
./.venv/Scripts/python.exe manage.py createsuperuser  # optional, for /admin
./.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000
```

- API:      http://127.0.0.1:8000/api/v1/config
- Health:   http://127.0.0.1:8000/api/v1/health
- Admin:    http://127.0.0.1:8000/admin (reports review, quarantine restore, data)
- Dev OTP:  `424242` (fixed in DEBUG; prod emails a random code)

### Verify everything

```bash
./.venv/Scripts/python.exe -m pytest        # 39 business-rule tests
./.venv/Scripts/python.exe smoke_test.py    # 26-check end-to-end pass
./.venv/Scripts/ruff.exe check apps config  # lint: 0 findings
```

### Point the Flutter app at this server

```bash
cd ../time_need_app
flutter run --dart-define=NEEDY_USE_API=true \
            --dart-define=NEEDY_API_URL=http://10.0.2.2:8000   # Android emulator
# LAN phone: http://<your-pc-ip>:8000   (ALLOWED_HOSTS covers 192.168.x.x in dev)
# Web:       http://localhost:8000 (CORS already allows :8090 serve-phone.js)
```

No define (or offline) → the app runs in demo mode on `MockBackend`. The
swap is one flag; both backends implement `BackendContract`.

## Docker (optional, Postgres included)

```bash
docker compose up        # API on :8000, Postgres on :5432, auto-seeded
```

## Deploy free (Render + Neon, ~15 minutes)

1. **Neon** (free Postgres, doesn't expire): create project → copy the
   pooled connection string.
2. **Render**: New → Web Service → connect this repo.
   - Root dir: `backend` · Environment: `Docker` · Instance: Free
   - Env vars:
     - `DJANGO_SETTINGS_MODULE=config.settings.prod`
     - `SECRET_KEY=<50+ random chars>`
     - `DATABASE_URL=<neon connection string>`
     - `ALLOWED_HOSTS=your-service.onrender.com`
     - `CORS_ALLOWED_ORIGINS=https://your-web-host` (and `http://localhost:8090` for the phone preview)
3. Deploy — `entrypoint.sh` migrates and (with `SEED_DEMO=1`) seeds.
4. APK: `flutter build apk --release --dart-define=NEEDY_USE_API=true --dart-define=NEEDY_API_URL=https://your-service.onrender.com`

Free-tier notes: Render spins down after 15 min idle (first request
wakes it, ~50 s); Neon free Postgres does **not** pause like Supabase's.
Upgrade triggers are pre-agreed in STANDARDS.md §6.

## Email OTP in production

Set in Render env (Resend free tier = 100 mails/day):
`EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
`EMAIL_HOST=smtp.resend.com`, `EMAIL_PORT=587`,
`EMAIL_HOST_USER=resend`, `EMAIL_HOST_PASSWORD=<api-key>`.
Until then, dev prints codes to the console.

## Layout

```
config/   settings split (base/dev/test/prod), urls, asgi/wsgi
apps/
  core/          base models, moderation engine, geo, pagination, errors, health/config, seed_demo
  accounts/      Member, OTP auth, JWT, /me, badges
  posts/         Task (all 6 kinds), applications, saves, ratings, feed
  chat/          rooms, messages (since_seq polling), unread counters
  auctions/      auctions, row-locked bids, buy-now, lazy close
  engagement/    karma ledger, perks, challenges, ideas, radar
  moderation/    reports (auto-quarantine), blocks, audit trail
  notifications/ notification centre
```
