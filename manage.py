#!/usr/bin/env python
"""needy backend — Django management entrypoint.

Run everything from the ``backend/`` folder:

    python manage.py runserver
    python manage.py migrate
    python manage.py seed_demo
"""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate the backend virtualenv first "
            "(see README.md → Quickstart)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
