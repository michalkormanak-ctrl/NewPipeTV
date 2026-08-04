# Plán zálohovania a obnovy

## Produkcia (cieľový stav, Etapa 5+)

- **Cloud SQL for PostgreSQL**: automatizované denné zálohy + point-in-time
  recovery (PITR) s minimálne 30-dňovou históriou transakčných logov.
- **GCS (originály dokumentov)**: bucket s object versioning zapnutým;
  keďže `source_document` sa nikdy needituje (bod 5.3), strata objektu sa
  dá vždy zregenerovať opätovným ingestom, ale versioning chráni pred
  omylom pri zápise.
- **OpenSearch/vektorový index**: nezálohuje sa priamo - je to odvodená
  projekcia z Postgresu (ADR-0001) a reindexuje sa z primárneho registra.
- **Terraform state**: uložený v GCS bucket s versioning a state locking
  (Cloud Storage backend), nikdy lokálne.

## Postup obnovy po havárii (runbook, cieľový stav)

1. Obnoviť Cloud SQL z posledného automatizovaného zálohovania alebo PITR
   na konkrétny bod v čase.
2. Overiť integritu (počet riadkov v kľúčových tabuľkách, náhodná
   kontrola SHA-256 hash oproti GCS originálom).
3. Znovu vybudovať OpenSearch index z Postgresu (dávková úloha,
   Cloud Run Job).
4. Overiť `ingestion_run` protokol - identifikovať posledný úspešný beh
   pred výpadkom a spustiť ingest odznova od tohto bodu (idempotentné
   vzhľadom na `sha256` deduplikáciu).
5. Zverejniť `audit_event` záznam o obnove (kto, kedy, z akého bodu).

## Retenčné pravidlá

- `audit_event`: nikdy sa nemaže (compliance).
- `source_document`: nikdy sa nemaže, iba sa môže označiť ako
  `legal_status_note=informative` ak stratí záväznosť.
- `drafting_project`/`draft_version` v `personal_project` priestore: mazanie
  iba na explicitnú žiadosť vlastníka cez auditovaný endpoint (mimo pilotu).

## Stav v tomto pilote

Lokálny Docker Compose bez zálohovania (vývojové dáta, nie produkčné).
Vyššie uvedené je plán pre produkčné nasadenie (Etapa 5+), nie súčasný stav.
