# Používateľská príručka (pilot)

## Čo pilot vie

- Prijať dopyt s právnym odkazom (napr. `§ 31 ods. 2`, `paragraf 31 odsek 2`,
  `zákon č. 500/2022 Z. z.`) a nájsť presne zodpovedajúce ustanovenie
  účinné k zadanému (alebo dnešnému) dátumu.
- Ak dátum nezadáte, systém to **explicitne povie** v odpovedi
  (`as_of_note`) - v súlade s bodom 3.3 zadania.
- Ak sa nenájde presná zhoda podľa odkazu, spadne na jednoduché fulltextové
  vyhľadávanie v uloženom obsahu.
- Prijať **jednoduchý pokyn v prirodzenom jazyku** (bod 2 zadania) cez
  režim "Legislatívny projekt", nájsť cieľové ustanovenie, aplikovať
  prípadné novelizačné body a vytvoriť výstupný balík so sekciami A-L
  (manažérske zhrnutie, právny stav, kontrolná správa, otvorené otázky,
  zdroje). Ak pokyn neobsahuje dosť informácií (napr. chýba konkrétny §),
  systém sa **spýta**, nevymyslí umiestnenie zmeny.
- Exportovať výsledný balík do Markdown, HTML, DOCX, PDF alebo XLSX
  (kontrolná správa/pripomienky) priamo z webového rozhrania.

## Čo pilot (zatiaľ) nevie

Pozri `docs/known-limitations.md` - najmä: **žiadne reálne právne dáta
nie sú načítané**, **žiadne skutočné LLM generovanie** (manažérske
zhrnutie, varianty a dôvodová správa bežia nad `FakeLLMProvider` - text je
len demonštračný, nie skutočná právna analýza).

## Ako použiť API

Právna rešerš:

```bash
curl "http://localhost:8000/api/v1/search?q=%C2%A7%2031%20ods.%202&as_of=2024-01-01"
```

Legislatívny projekt z voľného textu:

```bash
curl -X POST http://localhost:8000/api/v1/legislative-project/from-text \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Zmeň § 12 zákona č. 500/2022 Z. z.", "as_of": "2024-01-01"}'
```

Export balíka (vezmite JSON odpoveď vyššie a pošlite ju ako telo):

```bash
curl -X POST http://localhost:8000/api/v1/export/markdown \
  -H "Content-Type: application/json" \
  -d @balik.json
```

Odpoveď na `/search` obsahuje pre každý výsledok: presnú citáciu predpisu,
označenie ustanovenia, text, dátum účinnosti a upozornenie na prípadnú
pracovnú konsolidáciu.

## Ako naplniť pilot vlastnými testovacími dátami

Kým nie je k dispozícii povolený sieťový prístup na Slov-Lex (pozri
`docs/risks.md`), dáta je možné vložiť manuálne cez SQLAlchemy session
(pozri `backend/tests/test_search_service.py::_seed` ako príklad) alebo
napísaním skriptu, ktorý zoberie výstup `app.parser.structure_parser` a
uloží ho cez modely v `app/models/`.

## Webové rozhranie

`frontend/index.html` má dve záložky:

1. **Právna rešerš** - dopyt + dátum, zobrazí výsledky s citáciami.
2. **Legislatívny projekt** - textové pole na voľný pokyn, po spustení
   zobrazí celý výstupný balík (A, B, J, K, L) a tlačidlá na export.

Otvorte súbor priamo v prehliadači pri bežiacom backende na
`localhost:8000` (upravte `API_BASE` v súbore, ak backend beží inde).
Backend musí mať povolené CORS pre origin frontendu - v `app/main.py` je
to v pilote nastavené na `allow_origins=["*"]` **iba pre lokálny vývoj**,
v produkcii treba obmedziť na konkrétny zoznam originov (`docs/security.md`).

Nepredstavuje plné UI zo sekcie 15 zadania (chýba napr. porovnanie
predpisov/časových verzií, spracovanie pripomienok) - zoznam v
`docs/known-limitations.md`.
