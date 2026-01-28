# Tobacco Leaf Disease Tool - Repo Skeleton (Postgres)

This repository contains a minimal multi-service skeleton for development:
- Django backend (PostgreSQL)
- React web admin (development server)
- ML workspace (Jupyter)

Run locally (requires Docker Desktop):

1. Copy `.env.example` to `.env` and edit if needed.
2. Build and start containers:
   ```bash
   docker compose up --build
   ```
3. Services:
   - Django backend: http://localhost:8000
   - React web admin: http://localhost:3000
   - Jupyter (ML): http://localhost:8888 (token printed in logs)
   - Postgres: localhost:5432 (user: postgres / password: postgres by default)

Notes:
- The backend connects to the Postgres container named `db`.
- Media uploads are persisted in `./backend/media`.
- Postgres data is stored in a named Docker volume `postgres_data`.
- This skeleton is for development/demo purposes only.

