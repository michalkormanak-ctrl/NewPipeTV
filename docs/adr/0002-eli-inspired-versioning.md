# ADR-0002: Model verziovania inšpirovaný ELI/FRBR (work–expression–manifestation)

## Stav
Prijaté

## Kontext
Právny predpis existuje v čase vo viacerých rovinách: abstraktné "dielo"
(zákon č. 500/2022 Z. z. ako taký), jeho "vyjadrenie" v konkrétnom jazyku a
konkrétnom časovom bode (znenie účinné od–do), a konkrétny "nosič"
(vyhlásené PDF v Zbierke zákonov, HTML na Slov-Lex). Zámena týchto rovín je
najčastejšia príčina chýb v právnych informačných systémoch (napr.
prezentovanie historického znenia ako aktuálneho).

## Rozhodnutie
Prevzatý FRBR/ELI vzor so 4 úrovňami:
- `legal_instrument` (work) – predpis ako právna entita naprieč časom,
- `legal_expression` (expression) – jazyková/časová verzia (napr. znenie
  účinné od 1.1.2023),
- `legal_manifestation` (manifestation) – konkrétny formát/nosič (PDF, HTML),
- `legal_version` – explicitný záznam časového intervalu platnosti/účinnosti
  naviazaný na `legal_expression`, používaný point-in-time modulom.

`provision` a `provision_version` zrkadlia rovnaký vzor na úrovni
ustanovení, aby bolo možné zistiť znenie konkrétneho § k ľubovoľnému dátumu
bez nutnosti prechádzať celý dokument.

## Dôsledky
- Každý dopyt na obsah musí niesť `as_of` dátum (alebo explicitne zvoliť
  "aktuálne" = dnešný dátum), inak dotaz nie je jednoznačný.
- Vyššia zložitosť schémy oproti plochému modelu "jeden text = jeden
  predpis", ale toto je nevyhnutné pre bod 3.3 a sekciu 7 zadania.
