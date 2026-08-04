"""Legislatívno-technické validátory (Kontrola A, sekcia 13; akceptačné testy
18.3 body 8-9,12)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.search.normalize import normalize_reference

_INTERNAL_REF_RE = re.compile(r"§\s*\d+[a-z]?(?:\s*ods\.?\s*\d+)?")
_MISSING_DATA_MARKERS = ("[DOPLNIŤ", "[doplniť")


@dataclass(frozen=True)
class ValidationFinding:
    check: str
    severity: str  # kriticke | zavazne | stredne | legislativno_technicke | odporucanie
    message: str
    location: str | None = None


def check_internal_references(text: str, known_paragraf_labels: set[str]) -> list[ValidationFinding]:
    """Akceptačný test 18.3/8: odhaliť neexistujúci vnútorný odkaz."""
    findings: list[ValidationFinding] = []
    for match in _INTERNAL_REF_RE.finditer(text):
        ref = normalize_reference(match.group(0))
        if ref.unit == "§" and ref.number and ref.number not in known_paragraf_labels:
            findings.append(
                ValidationFinding(
                    check="internal_reference",
                    severity="zavazne",
                    message=f"Odkaz na § {ref.number} neexistuje v tomto predpise.",
                    location=match.group(0),
                )
            )
    return findings


def check_undefined_terms(text: str, defined_terms: set[str], candidate_terms: set[str]) -> list[ValidationFinding]:
    """Akceptačný test 18.3/9: odhaliť nedefinovaný pojem.

    `candidate_terms` sú pojmy, ktoré text explicitne označuje ako
    legislatívne definované (napr. zvýraznené/úvodzovkami), ale ktoré sa
    nenachádzajú v `defined_terms` (z `term_definition` naprieč korpusom).
    """
    findings = []
    for term in candidate_terms:
        if term not in defined_terms and term in text:
            findings.append(
                ValidationFinding(
                    check="undefined_term",
                    severity="stredne",
                    message=f"Pojem '{term}' je použitý, ale nebola nájdená jeho definícia.",
                    location=term,
                )
            )
    return findings


def check_missing_data_markers(text: str) -> list[ValidationFinding]:
    """Akceptačný test 18.3/12: chýbajúce údaje musia byť označené, nie
    vymyslené. Táto kontrola len potvrdzuje prítomnosť správnej konvencie;
    neoznačené číselné tvrdenia sa nedajú spoľahlivo odhaliť pravidlom a
    vyžadujú LLM/human review (mimo pilotu)."""
    findings = []
    for marker in _MISSING_DATA_MARKERS:
        if marker in text:
            findings.append(
                ValidationFinding(
                    check="missing_data_marker_present",
                    severity="odporucanie",
                    message="Text obsahuje explicitne označené chýbajúce údaje - "
                    "musia byť doplnené gestorom pred finalizáciou.",
                    location=marker,
                )
            )
    return findings
