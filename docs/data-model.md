# Právny dátový model

Implementácia: `backend/app/models/*.py` (SQLAlchemy 2.0), migrácia
`backend/alembic/versions/0001_initial_schema.py`. Návrh vychádza z FRBR/ELI
princípov (ADR-0002) a zo zoznamu entít v sekcii 6.1 zadania.

## 1. Entity a ich účel

| Entita | Účel |
|---|---|
| `legal_instrument` | Predpis ako právna entita naprieč časom (work). Nesie bod 6.2 metadáta. |
| `legal_expression` | Jazyková/časová verzia predpisu (napr. znenie účinné od 1.1.2023). |
| `legal_manifestation` | Konkrétny nosič/formát (PDF v Zbierke, HTML na Slov-Lex) jednej expression. |
| `legal_version` | Explicitný interval platnosti/účinnosti pre point-in-time dotazy. |
| `provision` | Štrukturálna jednotka predpisu (časť/hlava/diel/oddiel/§/odsek/písmeno/bod/veta/príloha/položka/nadpis/poznámka), stromová štruktúra cez `parent_id`. |
| `provision_version` | Znenie konkrétneho ustanovenia platné v danom intervale. |
| `amendment` | Novelizačný bod – odkaz na `legal_instrument`, ktorý mení iný predpis, s presnou inštrukciou (nahradiť/vložiť/vypustiť/doplniť). |
| `legal_relation` | Hrana právneho grafu medzi dvomi predpismi/ustanoveniami (sekcia 8 – mení, dopĺňa, zrušuje, ...). |
| `citation` | Konkrétny odkaz nájdený v texte (na iný predpis/ustanovenie), normalizovaný. |
| `legislative_process` | Legislatívny proces (eLegislatíva) – materiál, gestor, stav. |
| `process_document` | Dokument v rámci procesu (dôvodová správa, doložky, znenie). |
| `comment` | Pripomienka k procesu (sekcia 12). |
| `comment_evaluation` | Vyhodnotenie pripomienky (akceptovaná/čiastočne/neakceptovaná, odôvodnenie). |
| `court_decision` | Súdne rozhodnutie (ÚS SR a i.), väzba cez `legal_relation`. |
| `eu_act` | Akt práva EÚ (CELEX/ELI), väzba cez `legal_relation` (preberá/vykonáva). |
| `term_definition` | Definícia pojmu s rozsahom platnosti (ktorý predpis/ustanovenie ho definuje a pre aký rozsah platí). |
| `source_document` | Evidencia každého stiahnutého originálu (bod 5.3 – hash, MIME, čas, zdroj). |
| `ingestion_run` | Protokol o behu ingestora (sekcia 17). |
| `validation_result` | Nález kontroly/validátora (legislatívnej, ústavnej, red-team, konsolidačný konflikt). |
| `drafting_project` | Legislatívny projekt (režim LEGISLATÍVNY_PROJEKT). |
| `draft_version` | Verzia pracovného návrhu v rámci projektu (workflow krokov 1–11). |
| `audit_event` | Bezpečnostný audit – každý prístup, export, LLM volanie (sekcia 16.2). |

## 2. Kľúčové invarianty

1. **Nemennosť originálu**: `source_document` sa nikdy needituje po vytvorení;
   nová verzia = nový riadok (bod 5.3, 17).
2. **Žiadne tiché preskočenie**: `amendment.application_status` môže byť
   `applied | conflict | pending`; `conflict` musí mať zodpovedajúci
   `validation_result` so `severity=critical` (sekcia 7).
3. **Časová jednoznačnosť**: `provision_version.effective_from`/`effective_to`
   sú `NOT NULL` okrem `effective_to` (NULL = stále účinné). Dotaz na obsah
   bez `as_of` parametra nie je v API povolený (vynucuje default = dnešný
   dátum + explicitný príznak v odpovedi, bod 3.3 zadania).
4. **Neistota vzťahov je explicitná**: `legal_relation.confidence` (`explicit`
   vs. `derived`) + `confidence_score` pre analyticky odvodené vzťahy
   (sekcia 8, posledný odstavec).
5. **Auditovateľnosť**: každý `audit_event` nesie `actor_id`, `action`,
   `resource_type`, `resource_id`, `model_used`, `prompt_hash`, `sources_used`
   (JSON zoznam `citation`/`source_document` ID), `timestamp`.

## 3. Diagram (zjednodušený, ER)

```
legal_instrument 1---N legal_expression 1---N legal_manifestation
       |                      |
       |                      1---N legal_version
       |
       1---N provision (self-referencing parent_id, strom)
                |
                1---N provision_version
                |
                N---N legal_relation (source/target = instrument alebo provision)
                |
                1---N citation (výskyt odkazu v texte)

legislative_process 1---N process_document
                     1---N comment 1---1 comment_evaluation

drafting_project 1---N draft_version 1---N validation_result

source_document 1---1 ingestion_run (posledný beh, ktorý ho vytvoril/potvrdil)
```

Plná definícia stĺpcov je v `backend/app/models/`.
