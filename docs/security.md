# Bezpečnostný model

## 1. Oddelenie priestorov (sekcia 16.1)

Štyri logické pracovné priestory, vynucované na úrovni riadku (`workspace`
stĺpec + Postgres Row-Level Security politiky v produkcii):

1. `public_legislation` – verejne dostupná legislatíva, bez obmedzení.
2. `internal_unclassified` – interné neutajované dokumenty rezortu.
3. `personal_project` – osobné pracovné projekty (`drafting_project`),
   viditeľné iba vlastníkovi a spolupracovníkom priradeným k projektu.
4. `sensitive_restricted` – citlivé dokumenty so zvýšeným režimom.
   **Nikdy sa nespracúvajú v bežnom cloudovom prostredí tohto systému**;
   utajované skutočnosti sú mimo rozsahu tohto systému úplne (bod 16.1 –
   explicitný zákaz). Tento priestor v pilote nemá žiadnu implementáciu
   spracovania – iba rezervované miesto v modeli, aby sa naň dalo neskôr
   odkázať pri návrhu samostatného izolovaného prostredia.

## 2. RBAC

Role (`app_user.roles`, pole reťazcov – v produkcii presunúť do
samostatnej `role`/`permission` tabuľky s M:N väzbou):

- `citizen_readonly` – iba verejná legislatíva, bez draftingu.
- `legislator` – tvorba a úprava `drafting_project`.
- `constitutional_reviewer`, `eu_law_reviewer`, `data_protection_reviewer`,
  `security_reviewer`, `red_team_reviewer` – zápis do `validation_result`
  pre svoj `check_type`, princíp najmenších oprávnení (nemôžu meniť cudzí
  typ kontroly).
- `admin` – správa používateľov a ingest behov.

Vynucovanie: FastAPI dependency `require_role(*roles)` na každom endpointe,
ktorý mení stav (viď `backend/app/security/rbac.py`).

## 3. Autentifikácia a MFA

Pilot: jednoduchý nosič identity cez hlavičku overenú proti `app_user`
(zástupné riešenie pre lokálny vývoj). Produkcia: Google Identity Platform /
Cloud IAP s vynúteným MFA (bod 16.2) – mimo rozsahu pilotu, zaznamenané ako
implementačná úloha.

## 4. Šifrovanie

- V prenose: TLS všade (Cloud Run vynucuje HTTPS; lokálne cez Docker Compose
  TLS nie je nutné, keďže prevádzka je iba na loopback).
- V uložení: Cloud SQL/GCS šifrovanie na úrovni platformy (produkcia);
  lokálne heslá/API kľúče iba cez `.env` mimo git (`.gitignore`), v produkcii
  Secret Manager.

## 5. Audit (sekcia 16.2)

Každý:
- prístup k dátam (`action=query`),
- export (`action=export`),
- LLM/RAG odpoveď (`model_used`, `prompt_hash`, `sources_used`)

sa zapisuje do `audit_event` (viď `docs/data-model.md`). Audit log je
append-only (žiadny UPDATE/DELETE endpoint v API).

## 6. Ochrana pred prompt injection (sekcia 16.2, 10.x)

- Text stiahnutých dokumentov sa vždy vkladá do LLM promptu ako **dáta v
  ohraničenom bloku** (napr. `<document>...</document>`), nikdy zreťazené so
  systémovými inštrukciami.
- Systémový prompt explicitne inštruuje model ignorovať akékoľvek príkazy
  nájdené vo vloženom dokumente (implementované v
  `backend/app/llm/prompts.py`).
- `backend/app/security/sanitize.py` odstraňuje/escapuje sekvencie, ktoré sa
  bežne používajú na injekciu (napr. napodobeniny systémových značiek), pred
  vložením do kontextu.
- Testované v `tests/test_prompt_injection.py` – fixture dokument obsahuje
  vloženú inštrukciu ("Ignoruj predchádzajúce pokyny a ...") a test overuje,
  že sa nerešpektuje.

## 7. Zálohovanie a obnova

- Produkcia: Cloud SQL automatizované zálohy + point-in-time recovery;
  GCS má vlastnú verziovanú históriu objektov (a originály sa aj tak nikdy
  neprepisujú, iba pridávajú – bod 5.3).
- Retenčné pravidlá a mazanie na základe oprávnenia: `audit_event` sa
  nikdy nemaže; `drafting_project`/`personal_project` dáta sa mažú iba na
  žiadosť vlastníka cez audit-ovaný endpoint (mimo pilotu, plánované).

## 8. Známe obmedzenia pilotu

- RBAC v pilote je zjednodušený (bez MFA, bez IAM federácie).
- `sensitive_restricted` priestor nemá žiadnu implementáciu – zámerne, kým
  nebude k dispozícii samostatné izolované prostredie (bod 16.1, sekcia 7
  postupu realizácie).
- Šifrovanie v pilote spolieha na lokálne Docker siete, nie na produkčné
  cloudové šifrovanie.
