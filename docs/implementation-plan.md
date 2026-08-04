# Implementačný plán

Etapizácia podľa sekcie 20 zadania. Stav k 2026-08-04.

## Etapa 0 – Analýza a overenie zdrojov — **HOTOVO** (tento beh)
- `docs/00-source-map.md`, `docs/risks.md`, `docs/architecture.md`, `docs/adr/*`.

## Etapa 1 – Pilotný korpus — **ČIASTOČNE (funkčný pilot)**
Dodané v tomto behu:
- Dátový model (`backend/app/models/*`) + Alembic migrácia.
- Parser slovenskej právnej štruktúry (`backend/app/parser/structure_parser.py`)
  otestovaný na výňatku z Ústavy SR a zákona č. 400/2015 Z. z.
- Ingestor pre Slov-Lex (`backend/app/ingestion/slovlex.py`) – šetrný
  HTML getter, testovaný nad fixture súbormi (viď ADR-0003; live network
  bol v tomto sedení zablokovaný).

**Blokujúca úloha pred rozšírením pilotného korpusu:** živý smoke test
ingestora proti reálnemu `slov-lex.sk` v prostredí s povoleným sieťovým
prístupom + potvrdenie právnej prípustnosti spôsobu získavania (docs/risks.md
R1, R2).

Zvyšný pilotný korpus (aktuálne Legislatívne pravidlá vlády SR, zákon
č. 500/2022 Z. z., zákon č. 215/2004 Z. z., vykonávacie predpisy, vybrané
legislatívne procesy) sa načíta ingestorom hneď po odblokovaní sieťového
prístupu – kód je pripravený, dáta nie sú v tomto sedení stiahnuté.

## Etapa 2 – Vyhľadávanie a citácie — **ČIASTOČNE (funkčný pilot)**
- Normalizácia právnych odkazov (`backend/app/search/normalize.py`) +
  testy pre varianty zápisu § (bod 9.2).
- Presné vyhľadávanie nad Postgresom (`backend/app/search/service.py`).
- Fulltextové vyhľadávanie: pripravené rozhranie pre OpenSearch
  (`backend/app/search/opensearch_client.py`), beží v `docker-compose.yml`.
- Vektorové vyhľadávanie a reranking: **mimo pilotu** – vyžaduje
  embedding model / Vertex AI prístup (viď ADR-0004). Rozhranie pripravené
  (`backend/app/llm/base.py`).

## Etapa 3 – Legislatívny generátor — **NAVRHNUTÉ, ČIASTOČNE IMPLEMENTOVANÉ**
- Dátové entity (`drafting_project`, `draft_version`, `amendment`) hotové.
- Diff/aplikácia novelizačného bodu na aktuálne znenie: implementované
  (`backend/app/consolidation/apply_amendment.py`) s testami vrátane
  prípadu, ktorý sa má označiť ako konflikt.
- Generovanie paragrafového znenia a dôvodovej správy cez LLM: rozhranie
  pripravené (`backend/app/llm/`), reálne generovanie vyžaduje Vertex AI
  Gemini prístup (blokujúce, mimo pilotu) – v pilote beží nad
  `FakeLLMProvider` iba pre demonštráciu toku dát, **nie je pre skutočné
  právne použitie**.
- Exportná vrstva pre výstupný balík (sekcia 14 A-L) hotová a testovaná:
  Markdown/JSON/HTML/DOCX (`backend/app/export/`) + `POST /api/v1/export/*`.
  XLSX pre kontrolnú správu hotové s API endpointom; XLSX pre pripomienky
  (`to_comments_xlsx`) hotové, zatiaľ bez API endpointu. Chýba PDF export.
  Endpoint exportuje klientom zostavený balík - automatické zostavenie
  balíka z `DraftingProject` end-to-end vyžaduje LLM (pozri Etapa 3
  vyššie).

## Etapa 4 – Kontrolný systém — **NAVRHNUTÉ**
- `validation_result` entita a `check_type` enumerácia pre kontroly A–G
  (sekcia 13) hotové.
- Pravidlové validátory (legislatívno-technické: číslovanie, vnútorné
  odkazy, nedefinované pojmy) implementované a testované
  (`backend/app/validators/legislative.py`).
- Kontroly vyžadujúce právny úsudok (ústavná, EÚ, vecná, red-team) sú
  navrhnuté ako LLM-asistované kontroly s človekom v slučke – šablóny
  promptov pripravené, reálne vykonanie vyžaduje LLM prístup.

## Etapa 5 – Rozšírenie korpusu — **NEZAČATÉ** (vyžaduje Etapu 1 live test)

## Etapa 6 – Legislatívne procesy a pripomienky — **NEZAČATÉ**
Dátový model hotový (`legislative_process`, `comment`, `comment_evaluation`),
ingestor pre NR SR/eLegislatíva nie je implementovaný.

## Etapa 7 – Interné dokumenty — **NEZAČATÉ** (podmienené zavedením
prístupových pravidiel, bod 16.1 – vyžaduje rozhodnutie o klasifikácii)

## Ďalšie kroky (v poradí priority)
1. Získať prístup na overenie sieťovej dosiahnuteľnosti a právnej
   prípustnosti ingestu zo Slov-Lex (blokujúce).
2. Získať GCP projekt / Vertex AI prístup pre reálne LLM/embeddings
   (blokujúce pre Etapu 3–4 v produkčnej kvalite).
3. Live smoke test EUR-Lex CELLAR REST/SPARQL klienta (registrácia účtu).
4. Rozšíriť golden dataset (sekcia 18.1) o reálne stiahnuté dokumenty po
   bode 1.
5. Terraform moduly pre Cloud Run/Cloud SQL/GCS/Pub/Sub/Scheduler
   (kostra v `infra/terraform/`, `terraform plan` vyžaduje GCP projekt).
