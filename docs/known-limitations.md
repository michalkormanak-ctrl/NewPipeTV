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
   OpenSearch BM25 je naprogramované (`opensearch_client.py`), ale
   netestované end-to-end (vyžaduje bežiaci OpenSearch).
5. **Bez autentifikácie/MFA.** RBAC v pilote číta rolu z HTTP hlavičky bez
   overenia identity - nepoužívať mimo lokálneho vývoja.
6. **Bez exportnej vrstvy.** DOCX/PDF/XLSX export (sekcia 15) nie je v
   tomto pilote implementovaný.
7. **Bez frontendu s plnou funkcionalitou.** `frontend/` obsahuje iba
   minimálnu jednostránkovú demo pre `/api/v1/search`, nie všetky režimy
   zo sekcie 15.
8. **Legislatívny generátor (kroky 1-11 sekcie 11) nie je orchestrovaný
   end-to-end.** Stavebné bloky (dátový model, aplikácia novelizačných
   bodov, konsolidácia, validátory) existujú a sú testované samostatne;
   plné prepojenie na "jeden pokyn → kompletný balík" vyžaduje LLM prístup.
9. **`sensitive_restricted` pracovný priestor** (bod 16.1) nemá žiadnu
   implementáciu - zámerne, kým nebude definované izolované prostredie.
10. **Terraform (`infra/terraform/`) je nezaplikovaná kostra**, nie
    overená infraštruktúra - vyžaduje GCP projekt, ktorý v tomto sedení nie
    je k dispozícii.
11. **`comment_evaluation`, `court_decision`, `eu_act`, `legislative_process`
    ingestory nie sú implementované** - iba dátové entity pripravené na
    naplnenie v Etape 5-6.
