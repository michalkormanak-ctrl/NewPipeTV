# Postup aktualizácie právnych zdrojov (sekcia 17)

## Princípy

1. Aktualizácia **nikdy nemaže historickú verziu** - nová verzia je vždy
   nový riadok (`legal_expression`, `provision_version`, `source_document`).
2. Pri chybe sa **zachová predchádzajúca funkčná verzia**, chyba sa zapíše
   do `ingestion_run.error_log`, dotknutý predpis sa označí (napr.
   `LegalInstrument.status` zostáva na poslednej známej hodnote, nie sa
   neprepisuje odhadom) a beh je možné bezpečne zopakovať (idempotencia
   cez `sha256`).
3. Právny text sa **nikdy neopravuje odhadom** - pri nejasnosti sa
   ustanovenie označí `needs_review` (parser) alebo vytvorí
   `validation_result` so `status=open`.

## Plánovaný cyklus (cieľový stav, Cloud Scheduler)

| Úloha | Frekvencia | Poznámka |
|---|---|---|
| Úvodné úplné načítanie korpusu | jednorazovo | Etapa 1/5 |
| Kontrola nových predpisov | denne | diff zoznamu voči poslednému `ingestion_run` |
| Kontrola zmien existujúcich predpisov | denne | porovnanie `sha256` nového stiahnutia s posledným `source_document` |
| Kontrola nových časových verzií | denne | nové `legal_expression`/`provision_version` |
| Kontrola legislatívnych procesov | denne | Etapa 6 |
| Reindexácia (OpenSearch/vektor) | po každom úspešnom ingest behu | iba zmenené položky |

## Krok za krokom (jeden beh ingestora)

1. `IngestionRun` sa vytvorí so `status=running`.
2. Pre každý cieľový dokument: stiahnutie cez `RateLimitedSession`
   (rešpektuje `robots.txt`, rate limit, exponenciálny odklad).
3. Porovnanie `sha256` s posledným známym `source_document` pre rovnaký
   `source_url`/identifikátor:
   - zhoda -> žiadna zmena, iba sa aktualizuje `last_checked_at`,
   - rozdiel -> nový `source_document` riadok, spustí sa parser.
4. Parser vytvorí/aktualizuje `provision`/`provision_version` (nová verzia,
   stará zostáva s `effective_to` nastaveným).
5. Ak sa nájde novelizačný bod, ktorý sa nedá jednoznačne aplikovať,
   vytvorí sa `validation_result` (`check_type=konsolidacia`,
   `severity=kriticke`) - beh pokračuje ďalšími dokumentmi, tento konflikt
   sa nezahodí.
6. Reindexácia zmenených `provision_version` v OpenSearch.
7. `IngestionRun` sa uzavrie so súhrnom (`items_new`, `items_changed`,
   `items_failed`) a `status` (`success`/`partial_failure`/`failed`).

## Stav v tomto pilote

Krok 1-4 sú implementované a testované (`app/ingestion/`,
`app/parser/`). Kroky plánovania (Cloud Scheduler) a automatickej
reindexácie end-to-end sú navrhnuté, ale nie sú v tomto pilote spustené
(vyžadujú GCP/OpenSearch prostredie a povolený sieťový prístup na zdroje).
