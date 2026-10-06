#!/bin/sh
# nuvra backend container entrypoint.
set -e

echo "==> Waiting for database..."
python - <<'PY'
import os, sys, time

import dj_database_url
import psycopg

cfg = dj_database_url.config(default=os.environ.get("DATABASE_URL", ""))
if not cfg:
    print("No DATABASE_URL — skipping DB wait (SQLite).")
    sys.exit(0)

for attempt in range(30):
    try:
        psycopg.connect(
            host=cfg.get("HOST"), port=cfg.get("PORT") or 5432,
            user=cfg.get("USER"), password=cfg.get("PASSWORD"),
            dbname=cfg.get("NAME"), connect_timeout=3,
        ).close()
        print("Database is up.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"  attempt {attempt + 1}: {exc.__class__.__name__}; retrying…")
        time.sleep(2)
print("Database never came up.", file=sys.stderr)
sys.exit(1)
PY

echo "==> Applying migrations..."
python manage.py migrate --noinput

if [ "$SEED_DEMO" = "1" ]; then
    echo "==> Seeding demo content..."
    python manage.py seed_demo
fi

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting: $@"
exec "$@"
