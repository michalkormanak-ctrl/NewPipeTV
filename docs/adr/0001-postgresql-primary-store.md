# ADR-0001: PostgreSQL ako primárny register právneho obsahu

## Stav
Prijaté

## Kontext
Zadanie (bod 4.1) vyžaduje, aby Vertex AI (alebo akákoľvek vektorová/LLM
služba) nebola jedinou databázou právneho obsahu. Potrebujeme jeden zdroj
pravdy pre predpisy, verzie, vzťahy a identifikátory, ktorý je nezávislý od
konkrétneho poskytovateľa LLM.

## Rozhodnutie
Primárny register (`legal_instrument`, `provision`, `legal_relation`, ...)
je v PostgreSQL. Vyhľadávacie indexy (OpenSearch fulltext, pgvector/Vertex
AI Matching Engine vektorový index) sú odvodené projekcie, ktoré sa dajú
kedykoľvek znovu vybudovať z Postgresu. Žiadny index nesmie byť jediným
miestom, kde existuje niektorý údaj.

## Dôsledky
- Reindexácia je bezpečná operácia (žiadna strata dát).
- Výmena vektorovej služby (pgvector ↔ Vertex AI Matching Engine) nevyžaduje
  zmenu dátového modelu.
- Mierne vyššia latencia pri kombinovanom vyhľadávaní (nutnosť join-back do
  Postgresu po nájdení ID v indexe) – akceptované ako rozumný kompromis.
