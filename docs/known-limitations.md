# Známe obmedzenia (stav k 2026-08-04)

1. **Žiadne reálne právne dáta.** Databáza pilotu je prázdna okrem toho, čo
   si testy dočasne vytvoria v pamäti. Žiadny reálny predpis nebol v tomto
   sedení stiahnutý ani uložený - sieťový prístup na Slov-Lex/EUR-Lex bol
   zablokovaný (docs/risks.md R2).
2. **Neoverené HTML selektory Slov-Lex ingestora.** `app/ingestion/slovlex.py`
   používa tolerantné fallback selektory, ktoré neboli potvrdené proti
   živému webu. Nutná manuálna verifikácia pred prvým produkčným behom.
3. **Žiadne skutočné LLM volanie.** RAG/generátor beží iba nad
   `FakeLLMProvider`. Kvalita generovaných právnych textov, dôvodových
   správ, kontrol ústavnosti a red-teamu **nebola v praxi overená** -
   vyžaduje Vertex AI Gemini prístup (ADR-0004).
4. **Vektorové vyhľadávanie a reranking nie sú implementované.** Iba
   presné vyhľadávanie (Postgres) a jednoduchý ILIKE fulltext. Produkčné
   OpenSearch BM25 je naprogramované (`opensearch_client.py`) a jeho
   logika (volania klienta, spracovanie odpovede) je otestovaná nad
   falošným klientom (`tests/test_opensearch_client.py`) - **skutočný beh
   proti živej inštancii OpenSearch nebol overený**: `docker pull` je v
   tomto sedení zablokovaný egress politikou (potvrdené CONNECT 403 na
   `production.cloudfront.docker.com`, rovnaká kategória obmedzenia ako
   Slov-Lex/EUR-Lex, pozri docs/risks.md R13). Live smoke test je
   predpodmienkou produkčného nasadenia tejto vrstvy.
5. **Bez autentifikácie/MFA.** RBAC v pilote číta rolu z HTTP hlavičky bez
   overenia identity - nepoužívať mimo lokálneho vývoja.
6. **Exportná vrstva implementovaná pre všetkých 6 formátov zo sekcie 15**
   (Markdown/JSON/HTML/DOCX/PDF/XLSX) - `app/export/`,
   `POST /api/v1/export/*`, fungujú nad ľubovoľným
   `LegislativePackage`/zoznamom pripomienok zostaveným klientom. PDF
   exportér používa balený font DejaVu Sans (`app/export/fonts/`,
   licencia v `fonts/LICENSE`) kvôli správnemu zobrazeniu slovenskej
   diakritiky - vstavané reportlab fonty ju nepodporujú. Endpointy
   neorchestrujú *generovanie* obsahu balíka (to vyžaduje LLM, pozri bod 8
   nižšie) - iba serializujú už zostavené dáta.
7. **Bez frontendu s plnou funkcionalitou.** `frontend/` obsahuje iba
   minimálnu jednostránkovú demo pre `/api/v1/search`, nie všetky režimy
   zo sekcie 15 ani UI pre export.
8. **Legislatívny generátor je orchestrovaný end-to-end, ale iba nad
   `FakeLLMProvider`.** `app/generator/legislative_project.py` +
   `POST /api/v1/legislative-project` prepája vyhľadanie cieľového
   ustanovenia, aplikáciu novelizačných bodov (vrátane detekcie
   konfliktu), legislatívno-technické validátory a zostavenie
   `LegislativePackage` do jedného volania. **Textové sekcie, ktoré
   vyžadujú skutočný právny úsudok** (manažérske zhrnutie, varianty,
   dôvodová správa) sú generované cez `LLMProvider` rozhranie - pri
   `FakeLLMProvider` je výstup iba echo/demo, nie skutočná právna
   analýza. Krok 1 (interpretácia zadania) má odteraz **heuristickú
   extrakciu z voľného textu bez LLM**
   (`app/generator/instruction_interpreter.py`,
   `POST /api/v1/legislative-project/from-text`) - regexom nájde číslo/rok
   predpisu a odkaz na §/čl., overené priamo na príkladovom zadaní zo
   sekcie 2 master promptu (test `test_instruction_interpreter.py`). Ak sa
   nedá jednoznačne určiť predpis alebo ustanovenie, systém sa **spýta**,
   nevymyslí umiestnenie zmeny. Je to čisto pravidlová extrakcia (žiadne
   sémantické porozumenie cieľa, dotknutých osôb, sankcií a pod. - to
   stále vyžaduje LLM). Chýba aj: test potreby úpravy (krok 3),
   ústavnoprávna a EÚ kontrola (kroky 5-6, Kontroly B-G zo sekcie 13),
   detekcia nedefinovaných pojmov v generátore (vyžaduje kandidátne
   pojmy z NLP/LLM, zámerne nevolaná - pozri komentár v kóde), procesná
   mapa (krok 11).
9. **`sensitive_restricted` pracovný priestor** (bod 16.1) nemá žiadnu
   implementáciu - zámerne, kým nebude definované izolované prostredie.
10. **Terraform (`infra/terraform/`) je nezaplikovaná kostra**, nie
    overená infraštruktúra - vyžaduje GCP projekt, ktorý v tomto sedení nie
    je k dispozícii.
11. **`comment_evaluation`, `court_decision`, `eu_act`, `legislative_process`
    ingestory nie sú implementované** - iba dátové entity pripravené na
    naplnenie v Etape 5-6.
