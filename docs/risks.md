# Register rizík a neistôt (Etapa 0)

Legenda pravdepodobnosti/dopadu: N (nízka/nízky), S (stredná/stredný), V (vysoká/vysoký).

| # | Riziko | Pravd. | Dopad | Zmierenie |
|---|---|---|---|---|
| R1 | Slov-Lex nemá oficiálne API; scraping sa môže zmeniť bez upozornenia (zmena HTML štruktúry) | V | V | Parser oddelený od transportu, verziovaný extraktor, monitoring zlyhaní ingestu, alert pri páde parsovania nad prahovou hodnotou |
| R2 | Právne alebo zmluvné obmedzenia scrapovania Slov-Lex nie sú v tomto sedení overiteľné (network blocked) | V | V | Explicitne blokujúce – vyžaduje potvrdenie právnika/gestora pred produkčným behom |
| R3 | Automatická konsolidácia potichu nesprávne aplikuje novelizačný bod | S | V | Bod 7 zadania: konflikt sa NIKDY nepreskočí ticho, vždy sa označí ako `validation_result` s status=CONFLICT |
| R4 | LLM (Gemini/Vertex AI) generuje nepodložené právne tvrdenie ("halucinácia") | S | V | Povinná kontrola ukotvenia (grounding check) pred vydaním odpovede; tvrdenie bez citácie sa odstráni alebo označí |
| R5 | Zámena časovej verzie ustanovenia (historické znenie prezentované ako aktuálne) | S | V | Every provision_version nesie effective_from/effective_to; API vyžaduje explicitný as_of dátum vo všetkých dopytoch |
| R6 | Prompt injection vložený do stiahnutého právneho dokumentu | S | S | Text dokumentu sa vždy spracúva ako dáta (bod 16.2); systémový prompt LLM oddelený od obsahu dokumentu; sanitizácia/escaping pred vložením do kontextu |
| R7 | Chýbajúci prístup ku Google Cloud účtu/Vertex AI v tomto sedení | V | S | Pilot beží lokálne (Docker Compose, Postgres, OpenSearch); LLM/embeddings vrstva je abstrahovaná cez rozhranie vymeniteľné za Vertex AI po získaní prístupu |
| R8 | Nesprávne rozpoznanie právnej štruktúry (napr. rímske vs. arabské číslovanie, vnorené písmená) | S | S | Parser testovaný na golden datasete (Ústava SR, zákon 400/2015); neznáme vzory sa označia ako `needs_review`, nezahodia sa |
| R9 | Rozsah zadania (celý produkčný systém) presahuje možnosti jedného vývojového sedenia | V | S | Etapizácia podľa sekcie 20; tento beh dodáva Etapu 0 + časť Etapy 1–3 ako funkčný pilot, zvyšok je v implementačnom pláne |
| R10 | Osobné/citlivé údaje (napr. VS oprávnenia v ukážkovom zadaní) si vyžadujú osobitný bezpečnostný režim | S | V | Sekcia 16.1 – oddelené priestory; citlivé/utajované dokumenty sa nesmú spracúvať v bežnom cloude; v pilote nie sú takéto dáta prítomné |
| R11 | Duplicitná/nekonzistentná terminológia naprieč predpismi | S | N | `term_definition` entita s väzbou na predpis a rozsah platnosti; validátor kontroluje nedefinované pojmy |
| R12 | Zmena Legislatívnych pravidiel vlády SR alebo procesných krokov NR SR | S | S | Procesná mapa (bod 11) sa generuje z aktuálne overených pravidiel, nie je hardcoded na trvalo |
| R13 | `docker pull` je v tomto sedení zablokovaný egress politikou (potvrdené: CONNECT na `production.cloudfront.docker.com` vrátil 403) | V | S | OpenSearch end-to-end beh (`docker-compose.yml`) nemožno v tomto sedení reálne overiť. `OpenSearchIndex` wrapper je otestovaný nad falošným klientom (`tests/test_opensearch_client.py`) - overuje volania/spracovanie odpovede, nie skutočné správanie Lucene BM25. Live smoke test je predpodmienkou produkčného nasadenia (rovnaká kategória blokácie ako R2 - sieťová politika prostredia, nie chyba kódu) |

## Neistoty vyžadujúce rozhodnutie človeka (blokujúce)

1. Potvrdenie právnej prípustnosti spôsobu získavania dát zo Slov-Lex (scraping vs. žiadosť o dátové rozhranie od MS SR).
2. Pridelenie GCP projektu / Vertex AI prístupu a rozpočtu pre produkčné nasadenie.
3. Registrácia účtu pre EUR-Lex webservice (SOAP) – kto je zodpovedná osoba/organizácia.
4. Rozhodnutie o retenčnej politike a klasifikácii citlivosti pre interné/utajované dokumenty (sekcia 16.1) pred rozšírením na Etapu 7.
