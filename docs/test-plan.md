# Testovací plán

## 1. Úrovne testov

- **Jednotkové** (`pytest`, `backend/tests/test_*.py`): parser, normalizácia
  odkazov, aplikácia novelizačného bodu, validátory, sanitizácia proti
  prompt injection.
- **Integračné**: FastAPI `TestClient` proti dočasnej SQLite/Postgres DB
  (`backend/tests/test_api_*.py`).
- **Golden dataset** (sekcia 18.1): `backend/tests/test_golden_dataset.py` -
  syntetický, ale koherentný korpus priamo v teste (nie samostatný
  fixture adresár), pokrývajúci všetkých 11 požadovaných scenárov -
  pozri sekciu 2a nižšie.

## 2a. Golden dataset (sekcia 18.1) - pokrytie 11 požadovaných scenárov

| # | Scenár | Test |
|---|---|---|
| 1 | Konkrétne vyhľadanie zákona | `test_search_service.py` |
| 2 | Konkrétne ustanovenie | `test_search_service.py` |
| 3 | Historická verzia | `test_point_in_time.py` |
| 4 | Novelizácia | `test_apply_amendment.py`, `test_generator_legislative_project.py` |
| 5 | Zrušené ustanovenie | `test_golden_dataset.py::test_repealed_provision_has_no_effective_version_after_repeal` |
| 6 | Rozdielna (odložená) účinnosť | `test_golden_dataset.py::test_delayed_effectiveness_of_single_provision_within_amendment` |
| 7 | Prechodné ustanovenie | `test_golden_dataset.py::test_transitional_provision_is_only_effective_within_its_window` |
| 8 | Odkaz na iný predpis | `test_golden_dataset.py::test_citation_resolves_to_target_provision_in_another_instrument` |
| 9 | Vykonávací predpis | `test_golden_dataset.py::test_implementing_regulation_relation` |
| 10 | Právny akt EÚ | `test_golden_dataset.py::test_eu_act_relation` |
| 11 | Pripomienka z legislatívneho procesu | `test_golden_dataset.py::test_legislative_process_comment_lifecycle` |

Doplnkovo (nie v pôvodnom zozname, ale rovnaká rodina modelov):
`test_court_decision_relation` (súdne rozhodnutie a väzba "bol predmetom
súdneho preskúmania"). Všetky scenáre 5-11 sú syntetické dáta priamo v
teste (žiadne reálne stiahnuté predpisy - pozri docs/risks.md).

## 2. Metriky (sekcia 18.2) a ako sa merajú v pilote

| Metrika | Meranie v pilote |
|---|---|
| Presnosť identifikácie predpisu/ustanovenia | `test_normalize.py` – presná zhoda regex normalizácie na sade variantov zápisu |
| Správnosť časovej verzie | `test_point_in_time.py` – dopyt s `as_of` musí vrátiť správny `provision_version` |
| Presnosť citácií | `test_search_service.py` – každý výsledok musí niesť plnú citáciu + zdroj |
| Podiel podložených tvrdení | `test_grounding.py` (mimo pilotu – vyžaduje LLM; zatiaľ iba kontrakt rozhrania) |
| Úspešnosť aplikácie novelizačných bodov | `test_apply_amendment.py` – vrátane prípadu konfliktu |
| Počet nevyriešených konsolidačných konfliktov | rovnaký test – konflikt sa NIKDY nezahodí ticho |
| Stabilita exportu | `test_export_*.py`, `test_api_export.py` – Markdown/JSON/HTML/DOCX/PDF/XLSX overené na štruktúrovaný roundtrip (nadpisy, tabuľky, escapovanie, diakritika v PDF) |

## 3. Akceptačné testy (sekcia 18.3) – stav pokrytia v tomto pilote

| # | Úloha | Stav v pilote |
|---|---|---|
| 1 | Nájsť presné znenie § účinné k dátumu | Implementované (`test_point_in_time.py`) na syntetických dátach |
| 2 | Porovnať dve časové verzie | Implementované (`consolidation/point_in_time.py::diff_versions`) |
| 3 | Určiť predpis, ktorý zmenu vykonal | Implementované (`ProvisionVersion.amended_by_id`) |
| 4 | Nájsť súvisiace definície v iných zákonoch | Implementované (`term_definition` + test) |
| 5 | Právna rešerš s presnými citáciami | Implementované (`search/service.py`) nad pilotným korpusom |
| 6 | Vytvoriť aplikovateľný novelizačný bod | Implementované (`test_apply_amendment.py`) |
| 7 | Vytvoriť pracovnú konsolidáciu | Implementované, vždy s povinným disclaimerom |
| 8 | Odhaliť neexistujúci vnútorný odkaz | Implementované (`validators/legislative.py::check_internal_references`) |
| 9 | Odhaliť nedefinovaný pojem | Implementované (`validators/legislative.py::check_undefined_terms`) |
| 10 | Odhaliť rozpor dôvodovej správy s paragrafovým znením | Navrhnuté, vyžaduje LLM (mimo pilotu) |
| 11 | Vytvoriť osobitnú časť dôvodovej správy | Navrhnuté, vyžaduje LLM (mimo pilotu) |
| 12 | Označiť chýbajúce údaje namiesto vymyslenia | Implementované (`[DOPLNIŤ ...]` konvencia, test v `test_validators.py`) |
| 13 | Zabrániť použitiu historického znenia ako aktuálneho | Implementované (API vyžaduje explicitný `as_of`, test `test_point_in_time.py`) |
| 14 | Odolať prompt injection v dokumente | Implementované (`test_prompt_injection.py`) |

Riadky 10–11 vyžadujú reálne LLM volanie a sú mimo rozsahu tohto pilotu
(blokujúce – chýba Vertex AI prístup). Zostávajúce riadky sú spustiteľné
príkazom nižšie bez akéhokoľvek cloudového účtu.

## 4. Spustenie testov

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Testy bežia proti SQLite in-memory (žiadny Docker potrebný pre jednotkové
testy). Integračné testy proti reálnemu Postgresu vyžadujú
`docker compose up -d db` (viď `README.md`).
