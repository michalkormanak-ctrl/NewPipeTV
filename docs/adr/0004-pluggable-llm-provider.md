# ADR-0004: Vymeniteľné LLM/embedding rozhranie, FakeLLMProvider pre testy

## Stav
Prijaté

## Kontext
Zadanie vyžaduje modulárnu architektúru, kde je možné vymeniť jazykový
model bez prestavby celého systému, a preferuje Gemini cez Vertex AI. V
tomto vývojovom sedení nie je k dispozícii GCP projekt ani Vertex AI
prístup.

## Rozhodnutie
`LLMProvider` a `EmbeddingProvider` sú abstraktné rozhrania
(`backend/app/llm/base.py`). `FakeLLMProvider`/`FakeEmbeddingProvider`
(deterministické, bez siete) sa používajú v testoch a lokálnom vývoji.
`VertexGeminiProvider` je pripravený ako adaptér so správnym rozhraním, ale
jeho reálne volanie vyžaduje `GOOGLE_APPLICATION_CREDENTIALS`/Vertex AI
projekt, ktorý nie je k dispozícii – označené ako blokujúca závislosť.

## Dôsledky
- Celý RAG/generátor pipeline je testovateľný a demonštrovateľný bez
  cloudového účtu.
- Kvalita skutočných LLM odpovedí (Gemini) nie je v tomto pilote overená;
  overí sa až po pridelení prístupu.
