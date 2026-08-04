# Slovenský AI legislatívny systém — pilot (Etapa 0–3)

Tento repozitár obsahuje **Etapu 0** (analýza, architektúra, dátový model,
bezpečnostný model, plány) a funkčný **lokálny pilot** slovenského AI
legislatívneho systému podľa zadania. Cieľom je autoritatívne, dohľadateľné
a časovo presné právne vyhľadávanie a asistovaná tvorba legislatívy — nikdy
vymyslené právo.

**Predtým než čokoľvek použijete, prečítajte si
[`docs/known-limitations.md`](docs/known-limitations.md).** Tento pilot
**neobsahuje žiadne reálne overené právne dáta** — sieťový prístup na
Slov-Lex a EUR-Lex bol v tomto vývojovom sedení zablokovaný egress
politikou prostredia (pozri [`docs/risks.md`](docs/risks.md), R2).

## Rýchly štart

```bash
docker compose up -d db opensearch
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
pytest -v                 # 69 testov, bez potreby bežiaceho Docker/DB
uvicorn app.main:app --reload
```

Podrobnosti: [`docs/operations-guide.md`](docs/operations-guide.md).

## Dokumentácia (začnite tu)

| Dokument | Obsah |
|---|---|
| [`docs/00-source-map.md`](docs/00-source-map.md) | Overená mapa oficiálnych dátových zdrojov (Etapa 0, krok 1) |
| [`docs/risks.md`](docs/risks.md) | Register rizík a blokujúce neistoty vyžadujúce rozhodnutie človeka |
| [`docs/architecture.md`](docs/architecture.md) | Vrstvy systému, dátové toky, nasadenie |
| [`docs/adr/`](docs/adr) | Architecture Decision Records |
| [`docs/data-model.md`](docs/data-model.md) | Právny dátový model (ELI/FRBR-inšpirovaný) |
| [`docs/security.md`](docs/security.md) | RBAC, oddelenie priestorov, audit, ochrana pred prompt injection |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Stav podľa etáp (sekcia 20 zadania) |
| [`docs/test-plan.md`](docs/test-plan.md) | Testovacia stratégia, pokrytie akceptačných kritérií (18.3) |
| [`docs/known-limitations.md`](docs/known-limitations.md) | Čo pilot **nevie** |
| [`docs/backup-recovery.md`](docs/backup-recovery.md) | Plán zálohovania a obnovy |
| [`docs/update-procedure.md`](docs/update-procedure.md) | Postup aktualizácie právnych zdrojov |
| [`docs/operations-guide.md`](docs/operations-guide.md) | Prevádzková príručka |
| [`docs/user-guide.md`](docs/user-guide.md) | Používateľská príručka |

## Štruktúra repozitára

```
backend/
  app/
    models/        # SQLAlchemy modely - 22 entít (docs/data-model.md)
    parser/         # Rozklad slovenskej právnej štruktúry (§/odsek/písmeno/...)
    ingestion/       # Šetrný HTTP getter, rate limiting, Slov-Lex ingestor
    search/          # Normalizácia odkazov, presné+fulltext vyhľadávanie
    consolidation/    # Point-in-time modul, aplikácia novelizačných bodov
    validators/       # Legislatívno-technické kontroly (Kontrola A)
    llm/               # Vymeniteľné LLM rozhranie + FakeLLMProvider + prompty
    security/          # RBAC, sanitizácia proti prompt injection
    api/                # FastAPI routery (search, export, legislative-project)
    export/             # Markdown/JSON/HTML/DOCX/XLSX exportéry (sekcia 14/15)
    generator/           # Orchestrácia LEGISLATÍVNY_PROJEKT workflow (sekcia 11)
    schemas/             # Pydantic request/response modely (export, generator)
  alembic/            # Migrácie DB schémy
  tests/              # 69 pytest testov vrátane akceptačných kritérií 18.3
docs/                # Etapa 0 dokumentácia + ADR
frontend/            # Minimálna demo stránka pre /api/v1/search
infra/terraform/     # Nezaplikovaná kostra GCP infraštruktúry
docker-compose.yml   # Postgres + OpenSearch + API pre lokálny vývoj
```

## Čo je overiteľné hneď teraz

- `pytest -v` v `backend/` — 69 testov zelených, pokrývajú 12 z 14
  akceptačných kritérií zo sekcie 18.3 zadania bez potreby cloudového účtu
  (zvyšné 2 vyžadujú reálne LLM volanie, pozri `docs/test-plan.md`).
- `alembic upgrade head` vytvorí kompletnú schému (23 tabuliek) — overené
  proti SQLite aj koncepčne proti Postgresu (dialekt-portable typy).
- `uvicorn app.main:app` + `GET /health`, `GET /api/v1/search`,
  `POST /api/v1/export/{markdown,html,json,docx,xlsx/findings}`,
  `POST /api/v1/legislative-project` (celý workflow sekcie 11 nad
  `FakeLLMProvider` — pozri disclaimer v odpovedi, nie je pre skutočné
  právne použitie).

## Čo vyžaduje rozhodnutie/prístup človeka pred pokračovaním

Pozri `docs/risks.md`, sekcia "Neistoty vyžadujúce rozhodnutie človeka":
právna prípustnosť ingestu zo Slov-Lex, pridelenie GCP/Vertex AI prístupu,
registrácia EUR-Lex webservice účtu, klasifikácia citlivých dokumentov.
