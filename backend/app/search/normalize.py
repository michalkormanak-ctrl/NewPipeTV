"""Normalizácia rôznych zápisov toho istého právneho odkazu (bod 9.2 zadania).

Rozpoznáva napr.:
    § 31 ods. 2            -> §31/ods.2
    paragraf 31 odsek 2    -> §31/ods.2
    ust. § 31/2            -> §31/ods.2
    §31(2)                 -> §31/ods.2
    čl. 6 ods. 1 písm. c)  -> čl.6/ods.1/písm.c
    zákon č. 500/2022 Z. z.-> 500/2022
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_WS = r"\s*"

_INSTRUMENT_RE = re.compile(
    r"(?:z[áa]kon(?:a|om|e)?\s+)?(?:č\.?\s*)?(\d+)\s*/\s*(\d{4})\s*Z\.?\s*z\.?",
    re.IGNORECASE,
)

_UNIT_ALIASES = {
    "paragraf": "§",
    "ust": "§",
    "§": "§",
    "čl": "čl.",
    "clanok": "čl.",
    "článok": "čl.",
}

# "§ 31", "paragraf 31", "ust. § 31", "čl. 6"
_MAIN_UNIT_RE = re.compile(
    r"(paragraf|ust\.?|§|čl\.?|clanok|článok)" + _WS + r"(\d+[a-z]?)",
    re.IGNORECASE,
)

# Kompaktný zápis IHNEĎ po čísle paragrafu/článku: "§31(2)" alebo "§31/2".
_ODSEK_COMPACT_RE = re.compile(r"^" + _WS + r"[\(/]" + _WS + r"(\d+)" + _WS + r"\)?")
# Slovný zápis kdekoľvek v zvyšku textu: "ods. 2", "odsek 2".
_ODSEK_WORD_RE = re.compile(r"(?:ods\.?|odsek)" + _WS + r"(\d+)", re.IGNORECASE)

_PISMENO_RE = re.compile(
    r"(?:písm\.?|pism\.?|písmeno)" + _WS + r"([a-záäčďéíľĺňóôŕšťúýž])\)?", re.IGNORECASE
)
# Kompaktný zápis písmena hneď po odseku: "(2)c)" bez slova "písm.".
_PISMENO_COMPACT_RE = re.compile(r"^" + _WS + r"([a-záäčďéíľĺňóôŕšťúýž])\)")

_BOD_RE = re.compile(r"\bbod" + _WS + r"(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class LegalReference:
    unit: str | None = None  # "§" alebo "čl."
    number: str | None = None
    odsek: str | None = None
    pismeno: str | None = None
    bod: str | None = None
    instrument_number: str | None = None
    instrument_year: str | None = None

    def canonical(self) -> str:
        parts = []
        if self.unit and self.number:
            parts.append(f"{self.unit}{self.number}")
        if self.odsek:
            parts.append(f"ods.{self.odsek}")
        if self.pismeno:
            parts.append(f"písm.{self.pismeno}")
        if self.bod:
            parts.append(f"bod{self.bod}")
        ref = "/".join(parts)
        if self.instrument_number and self.instrument_year:
            suffix = f"{self.instrument_number}/{self.instrument_year} Z. z."
            ref = f"{ref} ({suffix})" if ref else suffix
        return ref


def normalize_reference(raw_text: str) -> LegalReference:
    text = raw_text.strip()

    main_match = _MAIN_UNIT_RE.search(text)

    unit = number = None
    odsek = pismeno = bod = None

    if main_match:
        raw_unit = main_match.group(1).lower().rstrip(".")
        unit = _UNIT_ALIASES.get(raw_unit, "§")
        number = main_match.group(2)

        remainder = text[main_match.end():]

        compact_match = _ODSEK_COMPACT_RE.match(remainder)
        word_match = _ODSEK_WORD_RE.search(remainder)
        # Kompaktný zápis hneď po čísle má prednosť (jednoznačnejší), inak
        # slovný zápis kdekoľvek v zvyšku (napr. "§ 31 ods. 2").
        odsek_match = compact_match or word_match
        if odsek_match:
            odsek = odsek_match.group(1)

        pismeno_match = _PISMENO_RE.search(remainder)
        if pismeno_match:
            pismeno = pismeno_match.group(1)
        elif compact_match:
            tail = remainder[compact_match.end():]
            compact_pismeno = _PISMENO_COMPACT_RE.match(tail)
            if compact_pismeno:
                pismeno = compact_pismeno.group(1)

        bod_match = _BOD_RE.search(remainder)
        if bod_match:
            bod = bod_match.group(1)

    # Kompaktný odsek je ukotvený hneď za číslom jednotky (^ na remainder),
    # takže sa nemôže zhodovať s "500/2022 Z. z." kdekoľvek inde v texte -
    # citáciu predpisu je preto bezpečné hľadať v celom pôvodnom texte.
    instrument_number = instrument_year = None
    instrument_match = _INSTRUMENT_RE.search(text)
    if instrument_match:
        instrument_number, instrument_year = instrument_match.groups()

    return LegalReference(
        unit=unit,
        number=number,
        odsek=odsek,
        pismeno=pismeno,
        bod=bod,
        instrument_number=instrument_number,
        instrument_year=instrument_year,
    )
