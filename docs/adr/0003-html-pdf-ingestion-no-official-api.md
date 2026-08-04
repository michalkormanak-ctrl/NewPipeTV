# ADR-0003: Ingestor Slov-Lex bez oficiálneho API (HTML/PDF getter)

## Stav
Prijaté (s výhradou – vyžaduje potvrdenie právnika pred produkčným behom)

## Kontext
Prieskum (docs/00-source-map.md) nenašiel oficiálne zdokumentované REST/XML
API od Ministerstva spravodlivosti SR pre Slov-Lex. Existujú iba komerčné
reexporty tretích strán, ktoré podľa pravidiel systému (3.1, 5.1) nemôžu
slúžiť ako primárny zdroj.

## Rozhodnutie
Ingestor pre Slov-Lex je implementovaný ako šetrný HTML/PDF getter:
- rate limiting (min. odstup medzi požiadavkami, konfigurovateľný),
- exponenciálny odklad pri chybách,
- kontrola `robots.txt` pred prvým behom (musí sa overiť pri nasadení –
  v tomto sedení bol sieťový prístup zablokovaný, pozri docs/risks.md R2),
  a kontrola sa vykonáva automaticky pri štarte ingestora (fail-closed,
  nie fail-open, ak `robots.txt` nie je dostupný),
  a
- evidencia zdroja, hash a metadát pre každý stiahnutý dokument
  (`source_document` entita).

Parser je oddelený od HTTP transportu (rozhranie `Fetcher`), takže zmenu
HTML štruktúry Slov-Lex je možné opraviť bez zásahu do zvyšku systému, a
testy bežia nad uloženými fixture súbormi, nie nad živou sieťou.

## Dôsledky
- Pilot nemôže byť v tomto sedení overený proti živému `slov-lex.sk`
  (network egress blocked). Live smoke test je predpodmienkou pre
  produkčné spustenie (viď implementation-plan.md, Etapa 1 – blokujúca
  úloha).
- Ak Ministerstvo spravodlivosti SR sprístupní oficiálne API, tento
  ingestor sa nahradí bez zmeny zvyšku pipeline (rovnaké `Fetcher`
  rozhranie).
