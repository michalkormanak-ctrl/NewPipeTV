"""Zdieľané testovacie fixtúry (nie samotné testy) pre exportné testy."""
from datetime import date

from app.export.package import LegislativePackage, SourceCitation
from app.validators.legislative import ValidationFinding


def sample_legislative_package() -> LegislativePackage:
    return LegislativePackage(
        title="Novela zákona č. 500/2022 Z. z. (testovací balík)",
        generated_at=date(2026, 8, 4),
        as_of_date=date(2026, 8, 4),
        as_of_was_default=True,
        executive_summary="Návrh dopĺňa oprávnenie získavať údaje z registra X.",
        current_legal_state="§ 12 zákona č. 500/2022 Z. z. v súčasnosti neupravuje...",
        problem_map="Cieľ: ...\nSubjekty: ...",
        variants="Variant 1: minimálny.\n\nVariant 2 (odporúčaný): vyvážený.",
        paragraph_wording="§ 12a\n(1) Text nového ustanovenia.",
        amendment_points="1. V § 12 sa za odsek 1 vkladá nový odsek 2.",
        consolidated_text="§ 12\n(1) Pôvodný text.\n(2) Nový text.",
        explanatory_memorandum="Všeobecná časť: ...\n\nOsobitná časť k bodu 1: ...",
        accompanying_documents="[DOPLNIŤ ODHAD ROZPOČTOVÉHO VPLYVU]",
        control_findings=[
            ValidationFinding(
                check="internal_reference",
                severity="zavazne",
                message="Odkaz na § 99 neexistuje.",
                location="§ 99",
            ),
            ValidationFinding(
                check="missing_data_marker_present",
                severity="odporucanie",
                message="Text obsahuje explicitne označené chýbajúce údaje.",
                location="[DOPLNIŤ",
            ),
        ],
        open_questions=["Aký má byť presný rozsah poskytovaných údajov?"],
        sources=[
            SourceCitation(
                instrument_full_citation="500/2022 Z. z.",
                provision_label="§ 12",
                source_url="https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2022/500/",
            )
        ],
    )
