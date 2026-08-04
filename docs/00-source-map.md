# Mapa dostupných oficiálnych dátových zdrojov (Etapa 0)

Stav overenia: **2026-08-04**. Overené v tejto relácii cez verejné vyhľadávanie (WebSearch).
Priamy sieťový prístup na `slov-lex.sk` a `eur-lex.europa.eu` bol v tejto relácii
**zablokovaný egress politikou prostredia** (HTTP 403 na CONNECT, potvrdené cez
`/root/.ccr/README.md` diagnostiku proxy). To znamená, že nasledujúce zistenia
vychádzajú z verejne indexovaného obsahu o týchto službách, nie z priamej
inšpekcie odpovedí API. **Pred produkčným nasadením musí niekto so sieťovým
prístupom overiť presné URL, formáty odpovedí a limity priamym volaním.**

## 1. Slov-Lex (Ministerstvo spravodlivosti SR)

- Skladá sa z dvoch prepojených systémov:
  - **eZbierka** – záväzné konsolidované elektronické znenia Zbierky zákonov SR,
  - **eLegislatíva** – riadenie legislatívneho procesu (medzirezortné pripomienkovanie,
    vládne materiály, uznesenia).
- **Zistenie:** Nenašli sme verejne zdokumentované, oficiálne REST/XML/JSON API
  priamo od Ministerstva spravodlivosti pre strojové čítanie obsahu Zbierky zákonov
  alebo eLegislatívy. Existujú iba **komerčné reexporty tretích strán**
  (napr. LexAPI/LexDATA – essential-data.sk), ktoré nie sú oficiálnym zdrojom
  a nemôžu byť použité ako autoritatívny prameň v zmysle pravidla 3.1 tohto
  systému (zákaz vymýšľania/nahradzovania oficiálneho zdroja).
- **Dôsledok pre návrh:** Ingestor pre Slov-Lex musí byť postavený ako **šetrný
  HTML/PDF getter** nad verejne prístupnými stránkami eZbierky a eLegislatívy
  (nie nad neexistujúcim API), s:
  - rešpektovaním `robots.txt` a podmienok používania (treba overiť priamo pri
    nasadení – v tejto relácii sme sa na `robots.txt` nedostali kvôli
    zablokovanému sieťovému prístupu),
  - rate-limitingom a exponenciálnym odkladom pri chybách,
  - prioritou HTML pred PDF a PDF pred OCR (bod 5.2 zadania),
  - evidenciou SHA-256 hash a metadát pri každom stiahnutí (bod 5.3).
- **Otvorená otázka pre gestora:** Ministerstvo spravodlivosti SR môže mať
  neverejné/zmluvné dátové rozhranie (napr. pre partnerské inštitúcie). Toto
  treba overiť priamym dopytom – nepredpokladať jeho existenciu.

## 2. Úrad vlády SR / Legislatívne pravidlá vlády SR

- Aktuálne znenie Legislatívnych pravidiel vlády SR je publikované ako
  dokument (uznesenie vlády), nie ako štruktúrovaný dátový zdroj.
- Ingestor: rovnaký prístup ako pri Slov-Lex – HTML/PDF, s overením dátumu
  poslednej aktualizácie pri každom behu (bod 11 zadania – proces sa nesmie
  brať ako nemenný).

## 3. Národná rada SR (NR SR)

- NR SR publikuje legislatívne dokumenty (návrhy zákonov, tlače, uznesenia,
  záznamy hlasovaní) na webovom portáli `nrsr.sk`.
- **Zistenie:** Verejne dostupný je "Systém na sledovanie legislatívneho
  procesu" (SSLP) – dokumentované rozhranie existuje, presný technický
  kontrakt (REST/SOAP/export) je potrebné overiť priamym prístupom.
- Do korpusu zaraďujeme ako sekundárny zdroj procesných dokumentov, previazaný
  na `legislative_process` a `process_document` entity.

## 4. Ústavný súd SR a súdne zdroje

- Rozhodnutia ÚS SR sú publikované na portáli ÚS SR (databáza rozhodnutí).
- Pre pilot: `court_decision` entita je pripravená v dátovom modeli, samotné
  napojenie na zdroj je mimo rozsahu pilotu (Etapa 5+).

## 5. EUR-Lex a Úradný vestník EÚ

- **Zistenie (dobre zdokumentované, na rozdiel od Slov-Lex):**
  - **SOAP webservice** – voľne dostupný po registrácii, umožňuje fulltextové
    vyhľadávanie ekvivalentné expertnému vyhľadávaniu na webe, vracia XML.
    Webservice sám osebe neumožňuje priame stiahnutie súborov dokumentov.
  - **CELLAR REST API** – umožňuje stiahnutie súborov dokumentov podľa
    identifikátora (CELEX, ELI).
  - **CELLAR SPARQL endpoint** – štruktúrované metadáta (CELEX, ELI, názov,
    dátum dokumentu, dátum nadobudnutia účinnosti, EuroVoc deskriptory,
    dostupné jazykové verzie).
  - Dokumentácia: `https://eur-lex.europa.eu/content/tools/webservices/`.
- **Dôsledok pre návrh:** EUR-Lex ingestor môže byť postavený priamo nad
  oficiálnym rozhraním (SPARQL pre metadáta + CELLAR REST pre obsah), čo je
  podstatne spoľahlivejšie než HTML scraping. Vyžaduje registráciu účtu
  (blokujúca závislosť – potrebné rozhodnutie/registrácia od prevádzkovateľa).

## 6. Ďalšie oficiálne registre verejnej správy

- `data.gov.sk` (Národný portál otvorených dát) – potenciálny zdroj
  štruktúrovaných dát verejnej správy; priamy prístup v tejto relácii nebol
  overiteľný (network blocked). Overiť v ďalšej etape.
- Register právnych predpisov obcí a VÚC – mimo rozsahu pilotu.

## 7. Sekundárne zdroje (iba doplnkovo, vždy označené ako sekundárne)

- Komerčné/súkromné právne informačné systémy (napr. ASPI, LexAPI/LexDATA) –
  môžu byť použité iba na krížovú kontrolu alebo ako pomocný nástroj na
  monitorovanie zmien, **nikdy** ako zdroj autoritatívneho znenia.

## 8. Zhrnutie rozhodnutí vyplývajúcich z tejto mapy

| Zdroj | Typ prístupu v produkcii | Spoľahlivosť | Stav v tomto pilote |
|---|---|---|---|
| Slov-Lex eZbierka | Šetrný HTML/PDF getter (žiadne oficiálne API nenájdené) | Vyžaduje priebežnú validáciu | Ingestor implementovaný nad fixture HTML, live endpoint neoverený (network blocked) |
| Slov-Lex eLegislatíva | Šetrný HTML/PDF getter | Vyžaduje priebežnú validáciu | Mimo pilotu (Etapa 6) |
| NR SR / SSLP | Web/rozhranie na overenie | Stredná | Mimo pilotu (Etapa 6) |
| ÚS SR | Web portál rozhodnutí | Stredná | Mimo pilotu (Etapa 5+) |
| EUR-Lex CELLAR | Oficiálne REST/SPARQL API | Vysoká | Klient naprogramovaný, live volanie neoverené (network blocked), potrebná registrácia |
| data.gov.sk | Na overenie | Neznáma | Mimo pilotu |

## 9. Explicitne nahlásený blokujúci stav

Podľa pravidla autonómnosti (sekcia 21 zadania) je toto zaznamenané ako
blokujúca okolnosť vyžadujúca rozhodnutie človeka:

> Sieťový prístup na `www.slov-lex.sk` a `eur-lex.europa.eu` je v aktuálnom
> vývojovom prostredí zablokovaný organizačnou egress politikou. Skutočné
> overenie URL, HTTP hlavičiek, `robots.txt`, licenčných podmienok a formátu
> odpovedí musí vykonať niekto s prístupom do prostredia, kde je tento
> prístup povolený, pred akýmkoľvek produkčným behom ingestora.
