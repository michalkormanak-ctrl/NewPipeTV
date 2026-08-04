"""Krok 1 (interpretácia zadania, sekcia 11) - heuristická extrakcia z
voľného textu, BEZ LLM.

Toto je zámerne obmedzený, pravidlový extraktor (regex nad
`app.search.normalize`), nie sémantické porozumenie. Vie nájsť explicitne
uvedené číslo/rok predpisu a odkaz na ustanovenie (§/čl.). Všetko ostatné,
čo krok 1 zadania vyžaduje (cieľ úpravy, dotknuté osoby, sankcie, väzby na
EÚ...), potrebuje skutočné porozumenie textu a je mimo dosahu regexu -
preto sa namiesto vymýšľania obsahu vracia zoznam otvorených otázok
(sekcia 11: "Pýtaj sa iba na otázky, bez ktorých nemožno vytvoriť právne
použiteľné riešenie.")."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from app.consolidation.apply_amendment import AmendmentInstruction
from app.export.package import LegislativePackage
from app.generator.legislative_project import DraftingRequest, run_legislative_project
from app.llm.base import LLMProvider
from app.search.normalize import normalize_reference
from app.validators.legislative import ValidationFinding


@dataclass(frozen=True)
class InterpretedInstruction:
    instrument_number: str | None
    instrument_year: int | None
    provision_reference: str | None
    blocking_questions: list[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        """Máme dosť na to, aby sme vedeli nájsť konkrétne ustanovenie a
        pokračovať krokom 2 (analýza súčasného stavu)."""
        return bool(self.instrument_number and self.instrument_year and self.provision_reference)


def interpret_instruction(text: str) -> InterpretedInstruction:
    reference = normalize_reference(text)
    questions: list[str] = []

    instrument_number = reference.instrument_number
    instrument_year = int(reference.instrument_year) if reference.instrument_year else None
    if not instrument_number or not instrument_year:
        questions.append(
            "Ktorý konkrétny predpis (číslo a rok, napr. '500/2022 Z. z.') sa má zmeniť? "
            "V texte pokynu sa nenašla jednoznačná citácia predpisu."
        )

    provision_reference = f"{reference.unit}{reference.number}" if reference.unit and reference.number else None
    if not provision_reference:
        questions.append(
            "Ktoré konkrétne ustanovenie (napr. '§ 12') sa má zmeniť, alebo do ktorého "
            "miesta predpisu sa má doplniť nové ustanovenie? V texte pokynu sa nenašiel "
            "jednoznačný odkaz na paragraf/článok - bez neho nemožno bezpečne nájsť a "
            "upraviť platné znenie (pravidlo 3.1 - žiadne vymyslené umiestnenie zmeny)."
        )

    return InterpretedInstruction(
        instrument_number=instrument_number,
        instrument_year=instrument_year,
        provision_reference=provision_reference,
        blocking_questions=questions,
    )


def build_drafting_request(
    text: str,
    interpreted: InterpretedInstruction,
    title: str | None = None,
    amendment_instructions: list[AmendmentInstruction] | None = None,
) -> DraftingRequest | None:
    """Vráti None, ak interpretácia nie je akcieschopná (chýbajúce
    blokujúce informácie) - volajúci musí najprv položiť otázky z
    `interpreted.blocking_questions`."""
    if not interpreted.is_actionable:
        return None

    return DraftingRequest(
        title=title or text.strip()[:120],
        user_instruction=text,
        target_instrument_number=interpreted.instrument_number,  # type: ignore[arg-type]
        target_instrument_year=interpreted.instrument_year,  # type: ignore[arg-type]
        target_provision_reference=interpreted.provision_reference,  # type: ignore[arg-type]
        amendment_instructions=amendment_instructions or [],
    )


def _blocked_package(text: str, title: str | None, questions: list[str]) -> LegislativePackage:
    today = date.today()
    return LegislativePackage(
        title=title or text.strip()[:120],
        generated_at=today,
        as_of_date=today,
        as_of_was_default=True,
        executive_summary=(
            "Pokyn sa nepodarilo jednoznačne interpretovať heuristickou extrakciou "
            "(bez LLM). Pred pokračovaním treba zodpovedať otvorené otázky nižšie "
            "(sekcia 11, krok 1 zadania - nepokračovať bez blokujúcich informácií)."
        ),
        current_legal_state="Neurčené - vyžaduje odpoveď na otvorenú otázku nižšie.",
        problem_map=text,
        variants="",
        control_findings=[
            ValidationFinding(
                check="instruction_not_actionable",
                severity="kriticke",
                message="Voľný pokyn neobsahuje dosť informácií na bezpečné pokračovanie.",
                location=None,
            )
        ],
        open_questions=questions,
        sources=[],
    )


def run_legislative_project_from_text(
    text: str,
    session: Session,
    llm: LLMProvider,
    as_of: date | None = None,
    title: str | None = None,
    amendment_instructions: list[AmendmentInstruction] | None = None,
) -> LegislativePackage:
    """Vstupný bod bližší k reálnemu použitiu (bod 2 zadania - "jednoduchý
    pokyn v prirodzenom jazyku"): interpretuje text a buď pokračuje celým
    workflow (`run_legislative_project`), alebo vráti balík s otvorenými
    otázkami, ak interpretácia nie je akcieschopná."""
    interpreted = interpret_instruction(text)
    request = build_drafting_request(text, interpreted, title=title, amendment_instructions=amendment_instructions)
    if request is None:
        return _blocked_package(text, title, interpreted.blocking_questions)
    return run_legislative_project(request, session, llm, as_of=as_of)
