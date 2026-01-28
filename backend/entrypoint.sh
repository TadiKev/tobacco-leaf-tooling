#!/usr/bin/env bash
set -e

echo "Waiting for Postgres to be ready..."

python - <<'PY'
import os, time, sys
import psycopg2
for i in range(30):
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('POSTGRES_DB','tobaccodb'),
            user=os.environ.get('POSTGRES_USER','postgres'),
            password=os.environ.get('POSTGRES_PASSWORD','postgres'),
            host=os.environ.get('POSTGRES_HOST','db'),
            port=os.environ.get('POSTGRES_PORT','5432'),
        )
        conn.close()
        print("Postgres is available")
        sys.exit(0)
    except Exception as e:
        print("Postgres not ready, retrying...", i)
        time.sleep(2)
print("Postgres did not become available in time, continuing anyway")
PY

# Apply database migrations
python manage.py migrate --noinput

# Collect static files (optional)
python manage.py collectstatic --noinput || true

# Start Gunicorn; fallback to runserver
gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 1 --log-level info || python manage.py runserver 0.0.0.0:8000
