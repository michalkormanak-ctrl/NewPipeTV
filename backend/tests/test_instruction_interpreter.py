"""Testy heuristickej extrakcie zadania (krok 1, sekcia 11) - vrátane
priamej regresie na príkladové zadanie z master promptu (sekcia 2)."""
from datetime import date

from app.generator.instruction_interpreter import (
    build_drafting_request,
    interpret_instruction,
    run_legislative_project_from_text,
)
from app.llm.fake import FakeLLMProvider
from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion

MASTER_PROMPT_EXAMPLE = (
    "Doplň do zákona č. 500/2022 Z. z. oprávnenie Vojenského spravodajstva "
    "získavať údaje z určeného registra. Nastav účel, rozsah údajov, spôsob "
    "poskytovania, evidenciu prístupov, kontrolu a ochranu údajov. Priprav "
    "kompletný legislatívny materiál."
)


def test_master_prompt_example_extracts_instrument_but_flags_missing_provision() -> None:
    """Príkladové zadanie zo sekcie 2 master promptu neobsahuje konkrétny §,
    takže systém sa musí spýtať, nie vymyslieť umiestnenie zmeny."""
    interpreted = interpret_instruction(MASTER_PROMPT_EXAMPLE)
    assert interpreted.instrument_number == "500"
    assert interpreted.instrument_year == 2022
    assert interpreted.provision_reference is None
    assert not interpreted.is_actionable
    assert any("ustanovenie" in q for q in interpreted.blocking_questions)
    # Otázka na chýbajúci PREDPIS (číslo/rok) sa nesmie objaviť - ten sa našiel.
    assert not any("číslo a rok" in q for q in interpreted.blocking_questions)


def test_no_instrument_and_no_provision_yields_both_questions() -> None:
    interpreted = interpret_instruction("Chcem zmeniť zákon o registri.")
    assert interpreted.instrument_number is None
    assert interpreted.provision_reference is None
    assert len(interpreted.blocking_questions) == 2


def test_clear_reference_is_actionable() -> None:
    interpreted = interpret_instruction("Zmeň § 12 zákona č. 500/2022 Z. z.")
    assert interpreted.is_actionable
    assert interpreted.blocking_questions == []
    request = build_drafting_request("Zmeň § 12 zákona č. 500/2022 Z. z.", interpreted)
    assert request is not None
    assert request.target_provision_reference == "§12"


def test_build_drafting_request_returns_none_when_not_actionable() -> None:
    interpreted = interpret_instruction("Nič konkrétne.")
    assert build_drafting_request("Nič konkrétne.", interpreted) is None


def _seed_instrument(db_session) -> None:
    instrument = LegalInstrument(
        number="500",
        year=2022,
        full_citation="500/2022 Z. z.",
        title="Testovací zákon (interpreter test)",
        instrument_type="zakon",
        legal_force="zakon",
        issuing_authority="Národná rada SR",
        status="ucinny",
        source="slov-lex",
    )
    db_session.add(instrument)
    db_session.flush()
    provision = Provision(
        instrument_id=instrument.id,
        unit_type="paragraf",
        order_index=1,
        label="§12",
        hierarchical_path="paragraf:12",
    )
    db_session.add(provision)
    db_session.flush()
    db_session.add(
        ProvisionVersion(
            provision_id=provision.id,
            text="(1) Pôvodné znenie.",
            text_hash="f" * 64,
            effective_from=date(2022, 1, 1),
            effective_to=None,
        )
    )
    db_session.commit()


def test_run_from_text_proceeds_when_actionable(db_session) -> None:
    _seed_instrument(db_session)
    package = run_legislative_project_from_text(
        "Zmeň § 12 zákona č. 500/2022 Z. z.", db_session, FakeLLMProvider(), as_of=date(2024, 1, 1)
    )
    assert "500/2022 Z. z." in package.current_legal_state
    assert package.open_questions == []


def test_run_from_text_blocks_on_master_prompt_example(db_session) -> None:
    package = run_legislative_project_from_text(
        MASTER_PROMPT_EXAMPLE, db_session, FakeLLMProvider(), as_of=date(2024, 1, 1)
    )
    assert package.current_legal_state == "Neurčené - vyžaduje odpoveď na otvorenú otázku nižšie."
    assert any("ustanovenie" in q for q in package.open_questions)
    assert any(f.check == "instruction_not_actionable" for f in package.control_findings)
