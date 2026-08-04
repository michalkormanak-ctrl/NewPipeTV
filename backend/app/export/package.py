"""Dátový model legislatívneho výstupného balíka (sekcia 14 zadania, body A-L).

Toto je exportovateľný, serializovateľný "snapshot" jedného
`DraftingProject` v danom bode workflow - nie ORM model. Exportéry
(markdown/json/html/docx/xlsx) pracujú nad touto štruktúrou, aby boli
nezávislé od DB session."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.validators.legislative import ValidationFinding

SEVERITY_ORDER = ("kriticke", "zavazne", "stredne", "legislativno_technicke", "odporucanie")

SEVERITY_LABELS = {
    "kriticke": "Kritické",
    "zavazne": "Závažné",
    "stredne": "Stredné",
    "legislativno_technicke": "Legislatívno-technické",
    "odporucanie": "Odporúčania",
}

# Poradie a nadpisy sekcií A-I (bez J-L, tie majú vlastnú logiku so
# zoskupením/tabuľkami) - zdieľané medzi markdown/html/docx exportérmi.
SECTION_TITLES = [
    ("executive_summary", "A. Manažérske zhrnutie"),
    ("current_legal_state", "B. Zistený právny stav"),
    ("problem_map", "C. Mapa problému"),
    ("variants", "D. Varianty riešenia"),
    ("paragraph_wording", "E. Paragrafové znenie"),
    ("amendment_points", "F. Novelizačné body"),
    ("consolidated_text", "G. Konsolidované znenie"),
    ("explanatory_memorandum", "H. Dôvodová správa"),
    ("accompanying_documents", "I. Ostatné sprievodné dokumenty"),
]


@dataclass(frozen=True)
class SourceCitation:
    """Bod L - presné ustanovenie a oficiálny zdroj pre podstatné tvrdenie."""

    instrument_full_citation: str
    provision_label: str | None
    source_url: str | None
    note: str | None = None


@dataclass(frozen=True)
class CommentExportRow:
    """Jeden riadok pripomienky pre XLSX export (sekcia 12 zadania) -
    nezávislé od ORM, mapuje sa z `Comment` + `CommentEvaluation`."""

    author: str
    target_provision_label: str | None
    comment_type: str  # zasadna | obycajna | hromadna
    is_fundamental: bool
    text: str
    proposed_wording: str | None
    justification: str | None
    thematic_category: str | None
    legal_argument: str | None
    result: str | None  # akceptovana | ciastocne_akceptovana | neakceptovana
    resolution_method: str | None
    final_wording: str | None


@dataclass
class LegislativePackage:
    """Zodpovedá bodom A-L sekcie 14 zadania. Polia, ktoré neboli v danom
    behu vytvorené (napr. nejde o novelu), zostávajú None/prázdne - nikdy sa
    nevypĺňajú vymysleným obsahom (pravidlo 3.1)."""

    title: str
    generated_at: date
    as_of_date: date
    as_of_was_default: bool

    executive_summary: str  # A - manažérske zhrnutie
    current_legal_state: str  # B - zistený právny stav
    problem_map: str  # C - mapa problému
    variants: str  # D - varianty riešenia
    paragraph_wording: str | None = None  # E - paragrafové znenie
    amendment_points: str | None = None  # F - novelizačné body
    consolidated_text: str | None = None  # G - konsolidované znenie
    explanatory_memorandum: str = ""  # H - dôvodová správa
    accompanying_documents: str = ""  # I - ostatné sprievodné dokumenty
    control_findings: list[ValidationFinding] = field(default_factory=list)  # J
    open_questions: list[str] = field(default_factory=list)  # K
    sources: list[SourceCitation] = field(default_factory=list)  # L

    disclaimer: str = (
        "Strojovo vytvorený pracovný legislatívny materiál. Pred použitím "
        "musí byť overený a schválený príslušným gestorom a prejsť "
        "viacstupňovou odbornou kontrolou (sekcia 13 zadania)."
    )

    def findings_by_severity(self) -> dict[str, list[ValidationFinding]]:
        grouped: dict[str, list[ValidationFinding]] = {s: [] for s in SEVERITY_ORDER}
        for finding in self.control_findings:
            grouped.setdefault(finding.severity, []).append(finding)
        return grouped
