# Architektúra systému

## 1. Prehľad vrstiev

```
┌─────────────────────────────────────────────────────────────────────┐
│ 11. Používateľské rozhranie (web frontend)                          │
├─────────────────────────────────────────────────────────────────────┤
│ 8. Legislatívny      9. Legislatívny        10. Exportná vrstva     │
│    generátor            validátor              (DOCX/PDF/MD/HTML/  │
│                                                  JSON/XLSX)          │
├─────────────────────────────────────────────────────────────────────┤
│ 7. RAG vrstva (retrieval → context building → grounding check)      │
├─────────────────────────────────────────────────────────────────────┤
│ 6. Vyhľadávacia vrstva (presné ID, fulltext/BM25, vektor, graf,     │
│    reranking, časové filtre)                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 5. Časový a konsolidačný modul (point-in-time, diff, konflikty)     │
├─────────────────────────────────────────────────────────────────────┤
│ 4. Právny dátový model (PostgreSQL – legal_instrument, provision,   │
│    legal_relation, ...)                                             │
├─────────────────────────────────────────────────────────────────────┤
│ 3. Vrstva parsovania (štruktúrny rozklad na časť/hlavu/.../vetu)    │
├─────────────────────────────────────────────────────────────────────┤
│ 2. Vrstva uchovávania originálov (GCS / lokálne object storage,     │
│    SHA-256, nemennosť)                                               │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Vrstva získavania dát (ingestory: Slov-Lex, EUR-Lex, NR SR, ...) │
└─────────────────────────────────────────────────────────────────────┘
        ▲                                                    ▲
        │                                                    │
12. Bezpečnostná a auditná vrstva (RBAC, MFA, audit log, retencia) – prierezová, dotýka sa všetkých vrstiev
```

## 2. Dátový tok (happy path pre právny dopyt)

```
používateľ → UI → API gateway (FastAPI)
   → RAG orchestrátor:
       1. klasifikácia dopytu (typ, jazyk, referencie)
       2. rozpoznanie dátumu (as_of)
       3. rozpoznanie odkazov (regex normalizácia § / čl. / zákon č.)
       4. presné vyhľadávanie (Postgres identifikátory)
       5. fulltext/BM25 (OpenSearch)
       6. vektorové vyhľadávanie (pgvector / Vertex AI Matching Engine)
       7. rozšírenie cez legal_relation graf
       8. reranking (cross-encoder alebo LLM reranker)
       9. načítanie plného kontextu ustanovenia (§ + okolie + definície)
      10. overenie časovej verzie (point-in-time modul)
      11. volanie LLM (Gemini cez Vertex AI, abstrahované cez LLMProvider rozhranie)
      12. kontrola ukotvenia (grounding check) – každé tvrdenie proti zdroju
      13. pripojenie citácií
   → odpoveď s citáciami + audit_event zápis
```

## 3. Dátový tok (legislatívny pracovný režim)

```
jednoduchý pokyn → interpretácia zadania (LLM + štruktúrovaný extraktor)
   → analýza súčasného stavu (retrieval nad dotknutými predpismi)
   → test potreby úpravy
   → varianty riešenia (LLM generuje, validátor kontroluje)
   → ústavnoprávna + EU kontrola (pravidlové + LLM kontroly)
   → paragrafové znenie (generátor + legislatívny validátor)
   → novelizačné body → strojová aplikácia na aktuálne znenie (diff engine)
   → konsolidované znenie (redline)
   → sprievodné dokumenty (dôvodová správa, doložky, ...)
   → viacstupňová kontrola A–G (sekcia 13) → oprava nálezov
   → exportný balík (DOCX/PDF/MD/HTML/JSON/XLSX)
```

## 4. Prečo modulárna architektúra s vymeniteľným LLM

- `LLMProvider` a `EmbeddingProvider` sú abstraktné rozhrania
  (`backend/app/llm/base.py`). Konkrétna implementácia pre Vertex AI Gemini
  je jeden adaptér; pre lokálny vývoj/testy sa používa `FakeLLMProvider`,
  aby testy bežali bez cloudového účtu (viď ADR-0004).
- Primárny register právneho obsahu je vždy PostgreSQL – vektorová služba
  (Vertex AI Matching Engine alebo pgvector) je iba index nad týmto obsahom,
  nikdy zdroj pravdy (bod 4.1 zadania).

## 5. Nasadenie (cieľový stav, Etapa 5+)

- Google Cloud: Cloud Run (API + workery), Cloud Run Jobs (dávkové
  spracovanie ingestu/konsolidácie), Cloud Scheduler (plánovanie),
  Pub/Sub (front udalostí medzi ingestom → parsovaním → indexovaním),
  Cloud SQL for PostgreSQL, GCS (originály), Secret Manager, Cloud Logging/
  Monitoring/Error Reporting. Terraform moduly v `infra/terraform/`
  (kostra pripravená, reálne `terraform apply` vyžaduje GCP projekt a
  oprávnenia, ktoré v tomto sedení nie sú k dispozícii – pozri `risks.md`).

## 6. Lokálny pilot (tento pilot, Etapa 1–3)

- `docker-compose.yml`: PostgreSQL 16 + OpenSearch (jednouzlový) + FastAPI.
- Vektorové vyhľadávanie: `pgvector` extenzia priamo v Postgrese (nahrádza
  Vertex AI Matching Engine pre lokálny vývoj – rozhranie je rovnaké).
- LLM: `FakeLLMProvider` pre testy; adaptér pre Vertex AI Gemini je
  pripravený, ale nevolaný (chýba prístup/API kľúč).
