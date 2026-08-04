# Prevádzková príručka (pilot)

## Lokálne spustenie

```bash
# 1. Infraštruktúra (Postgres + OpenSearch)
docker compose up -d db opensearch

# 2. Backend (lokálne, mimo Dockera - rýchlejší vývojový cyklus)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # uprav podľa potreby

# 3. Migrácia schémy
alembic upgrade head

# 4. Spustenie API
uvicorn app.main:app --reload

# 5. Testy (nevyžadujú bežiaci Docker - SQLite in-memory)
pytest -v
```

Alternatívne celý stack cez `docker compose up --build`.

## Kontrola stavu

- `GET /health` - liveness.
- `GET /api/v1/search?q=...&as_of=YYYY-MM-DD` - vyhľadávanie.

## Bežné prevádzkové úlohy (cieľový stav, mimo pilotu)

- Spustenie ingest behu: `Cloud Run Job` alebo lokálne
  `python -m app.ingestion.run_slovlex <url>` (skript na pridanie v
  ďalšej etape).
- Sledovanie zlyhaní: `ingestion_run.status != 'success'` a
  `validation_result.status = 'open'` so `severity IN ('kriticke','zavazne')`.
- Rotácia/kontrola `robots.txt` súhlasu: `RateLimitedSession` fail-closed
  pri nedostupnom `robots.txt` (viď ADR-0003) - zlyhania sa prejavia ako
  `ingestion_run.status = 'failed'` s dôvodom v `error_log`.

## Monitoring (cieľový stav)

Cloud Logging (štruktúrované logy z FastAPI + ingestorov), Cloud
Monitoring (alert na `ingestion_run` zlyhania, latenciu API), Error
Reporting (neošetrené výnimky). V pilote: štandardný `uvicorn`/Python log
na stdout.
