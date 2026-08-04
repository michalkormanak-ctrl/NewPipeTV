"""Orchestrácia režimu LEGISLATÍVNY_PROJEKT (sekcia 11 zadania).

Prepája moduly, ktoré sú inak testované samostatne (vyhľadávanie,
aplikácia novelizačných bodov, validátory, LLM, export) do jedného toku
"jednoduchý pokyn -> LegislativePackage". Textové sekcie, ktoré by za
normálnych okolností vyžadovali skutočný právny úsudok LLM (zhrnutie,
varianty, paragrafové znenie, dôvodová správa), sú v tomto pilote
generované cez `LLMProvider` rozhranie - pri `FakeLLMProvider` je výstup
zámerne označený ako demonštračný, NIE právne použiteľný (pravidlo 3.1,
docs/known-limitations.md bod 3 a 8).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consolidation.apply_amendment import AmendmentInstruction, ApplicationResult, apply_amendment
from app.consolidation.point_in_time import CONSOLIDATION_DISCLAIMER
from app.export.package import LegislativePackage, SourceCitation
from app.llm.base import LLMProvider
from app.llm.prompts import SYSTEM_PROMPT_LEGAL_QA, build_context_block
from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion
from app.search.normalize import normalize_reference
from app.security.sanitize import sanitize_document_text
from app.validators.legislative import (
    ValidationFinding,
    check_internal_references,
    check_missing_data_markers,
)


@dataclass
class DraftingRequest:
    """Vstup krok 1 (interpretácia zadania) - v pilote čiastočne
    štruktúrovaný ručne namiesto extrakcie z voľného textu (tá vyžaduje
    skutočné LLM, mimo pilotu)."""

    title: str
    user_instruction: str
    target_instrument_number: str
    target_instrument_year: int
    target_provision_reference: str  # napr. "§ 12"
    amendment_instructions: list[AmendmentInstruction] = field(default_factory=list)
    working_assumptions: list[str] = field(default_factory=list)
    requested_effective_date: date | None = None


def _find_target_provision(
    session: Session, request: DraftingRequest, as_of: date
) -> tuple[LegalInstrument, Provision, ProvisionVersion] | None:
    reference = normalize_reference(request.target_provision_reference)
    if not reference.unit or not reference.number:
        return None
    label = f"{reference.unit}{reference.number}"

    stmt = (
        select(LegalInstrument, Provision, ProvisionVersion)
        .join(Provision, Provision.instrument_id == LegalInstrument.id)
        .join(ProvisionVersion, ProvisionVersion.provision_id == Provision.id)
        .where(LegalInstrument.number == request.target_instrument_number)
        .where(LegalInstrument.year == request.target_instrument_year)
        .where(Provision.label == label)
        .where(ProvisionVersion.effective_from <= as_of)
        .where((ProvisionVersion.effective_to.is_(None)) | (ProvisionVersion.effective_to >= as_of))
    )
    row = session.execute(stmt).first()
    return tuple(row) if row else None


def _apply_all_amendments(
    text: str, instructions: list[AmendmentInstruction]
) -> tuple[str, list[ApplicationResult]]:
    current = text
    results: list[ApplicationResult] = []
    for instruction in instructions:
        result = apply_amendment(current, instruction)
        results.append(result)
        if result.status == "applied":
            current = result.resulting_text
        # Pri konflikte text NEMENÍME (bod 7 zadania - žiadne tiché
        # preskočenie), pokračujeme ďalšími bodmi nad pôvodným textom.
    return current, results


def run_legislative_project(
    request: DraftingRequest,
    session: Session,
    llm: LLMProvider,
    as_of: date | None = None,
) -> LegislativePackage:
    used_default_date = as_of is None
    effective_as_of = as_of or date.today()

    findings: list[ValidationFinding] = []
    open_questions: list[str] = []
    sources: list[SourceCitation] = []

    problem_map = request.user_instruction
    if request.working_assumptions:
        assumptions_text = "\n".join(f"- {a} [PRACOVNÝ PREDPOKLAD]" for a in request.working_assumptions)
        problem_map = f"{problem_map}\n\nPracovné predpoklady:\n{assumptions_text}"

    found = _find_target_provision(session, request, effective_as_of)

    if found is None:
        current_legal_state = (
            f"[NEOVERENÉ] Cieľové ustanovenie '{request.target_provision_reference}' "
            f"zákona č. {request.target_instrument_number}/{request.target_instrument_year} Z. z. "
            "sa nenašlo v registri k zadanému dátumu."
        )
        open_questions.append(
            "Cieľové ustanovenie nebolo nájdené v registri - nevyhnutné manuálne "
            "overenie gestorom pred pokračovaním (pravidlo 3.1 - žiadne vymyslené znenie)."
        )
        findings.append(
            ValidationFinding(
                check="target_provision_not_found",
                severity="kriticke",
                message="Cieľové ustanovenie sa nenašlo - nemožno bezpečne pokračovať v generovaní.",
                location=request.target_provision_reference,
            )
        )
        amendment_points_text = None
        consolidated_text = None
    else:
        instrument, provision, version = found
        current_legal_state = (
            f"{instrument.full_citation}, {provision.label}: {version.text}"
        )
        sources.append(
            SourceCitation(
                instrument_full_citation=instrument.full_citation,
                provision_label=provision.label,
                source_url=None,
                note=f"Znenie účinné od {version.effective_from.isoformat()}",
            )
        )

        known_labels = {
            row[0]
            for row in session.execute(
                select(Provision.label).where(Provision.instrument_id == instrument.id)
            ).all()
        }

        if request.amendment_instructions:
            new_text, results = _apply_all_amendments(version.text, request.amendment_instructions)
            amendment_lines = []
            for idx, (instruction, result) in enumerate(
                zip(request.amendment_instructions, results), start=1
            ):
                status_label = "aplikovaný" if result.status == "applied" else "KONFLIKT"
                amendment_lines.append(
                    f"{idx}. [{instruction.operation}] {status_label}"
                    + (f" - {result.note}" if result.note else "")
                )
                if result.status == "conflict":
                    findings.append(
                        ValidationFinding(
                            check="amendment_conflict",
                            severity="kriticke",
                            message=f"Novelizačný bod {idx} sa nedá jednoznačne aplikovať: {result.note}",
                            location=f"bod {idx}",
                        )
                    )
                    open_questions.append(
                        f"Novelizačný bod {idx} vyžaduje manuálnu úpravu pred aplikáciou "
                        "(automatická aplikácia zlyhala jednoznačnosťou zhody)."
                    )
            amendment_points_text = "\n".join(amendment_lines)
            consolidated_text = f"{new_text}\n\n{CONSOLIDATION_DISCLAIMER}"
        else:
            amendment_points_text = None
            consolidated_text = None

        # check_undefined_terms sa tu zámerne nevolá: vyžaduje zoznam
        # "kandidátnych pojmov" (termínov, ktoré text používa, akoby boli
        # legislatívne definované) - jeho spoľahlivé odvodenie z voľného
        # textu vyžaduje NLP/LLM asistenciu, ktorá je mimo tohto pilotu
        # (docs/known-limitations.md). Volanie s vymysleným zoznamom by
        # bolo zavádzajúce, preto sa radšej vynecháva.
        text_to_check = consolidated_text or version.text
        findings.extend(check_internal_references(text_to_check, known_labels))
        findings.extend(check_missing_data_markers(text_to_check))

    # Kroky vyžadujúce právny úsudok - v pilote cez LLMProvider rozhranie
    # (FakeLLMProvider produkuje jasne označený demonštračný text).
    context_block = build_context_block("current-legal-state", sanitize_document_text(current_legal_state))
    llm_response = llm.generate(
        system_prompt=SYSTEM_PROMPT_LEGAL_QA,
        user_prompt=request.user_instruction,
        context_documents=[context_block],
    )

    package = LegislativePackage(
        title=request.title,
        generated_at=date.today(),
        as_of_date=effective_as_of,
        as_of_was_default=used_default_date,
        executive_summary=llm_response.text,
        current_legal_state=current_legal_state,
        problem_map=problem_map,
        variants=llm_response.text,
        paragraph_wording=None,
        amendment_points=amendment_points_text,
        consolidated_text=consolidated_text,
        explanatory_memorandum=llm_response.text,
        accompanying_documents="[DOPLNIŤ - sprievodné dokumenty vyžadujú rozhodnutie gestora o rozsahu materiálu]",
        control_findings=findings,
        open_questions=open_questions,
        sources=sources,
    )
    return package
