# Používateľská príručka (pilot)

## Čo pilot vie

- Prijať dopyt s právnym odkazom (napr. `§ 31 ods. 2`, `paragraf 31 odsek 2`,
  `zákon č. 500/2022 Z. z.`) a nájsť presne zodpovedajúce ustanovenie
  účinné k zadanému (alebo dnešnému) dátumu.
- Ak dátum nezadáte, systém to **explicitne povie** v odpovedi
  (`as_of_note`) - v súlade s bodom 3.3 zadania.
- Ak sa nenájde presná zhoda podľa odkazu, spadne na jednoduché fulltextové
  vyhľadávanie v uloženom obsahu.

## Čo pilot (zatiaľ) nevie

Pozri `docs/known-limitations.md` - najmä: **žiadne reálne právne dáta
nie sú načítané**, **žiadne LLM generovanie** (dôvodové správy, návrhy
zákonov, kontroly ústavnosti bežia len na testovacích/prázdnych dátach),
**žiadny export do DOCX/PDF**.

## Ako použiť API

```bash
curl "http://localhost:8000/api/v1/search?q=%C2%A7%2031%20ods.%202&as_of=2024-01-01"
```

Odpoveď obsahuje pre každý výsledok: presnú citáciu predpisu, označenie
ustanovenia, text, dátum účinnosti a upozornenie na prípadnú pracovnú
konsolidáciu.

## Ako naplniť pilot vlastnými testovacími dátami

Kým nie je k dispozícii povolený sieťový prístup na Slov-Lex (pozri
`docs/risks.md`), dáta je možné vložiť manuálne cez SQLAlchemy session
(pozri `backend/tests/test_search_service.py::_seed` ako príklad) alebo
napísaním skriptu, ktorý zoberie výstup `app.parser.structure_parser` a
uloží ho cez modely v `app/models/`.

## Minimálne webové rozhranie

`frontend/index.html` je jednostránková demo pre `/api/v1/search` -
otvorte súbor v prehliadači pri bežiacom backende na `localhost:8000`
(alebo upravte `API_BASE` v súbore). Nepredstavuje plné UI zo sekcie 15
zadania - iba overenie, že API je dosiahnuteľné z prehliadača.
