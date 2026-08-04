"""End-to-end test orchestrácie LEGISLATÍVNY_PROJEKT (sekcia 11) nad
FakeLLMProvider - overuje, že moduly testované samostatne (vyhľadávanie,
aplikácia novelizačných bodov, validátory) fungujú spolu."""
from datetime import date

from app.consolidation.apply_amendment import AmendmentInstruction
from app.generator.legislative_project import DraftingRequest, run_legislative_project
from app.llm.fake import FakeLLMProvider
from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion


def _seed_instrument(db_session) -> tuple[LegalInstrument, Provision]:
    instrument = LegalInstrument(
        number="500",
        year=2022,
        full_citation="500/2022 Z. z.",
        title="Testovací zákon o registri (syntetický testovací záznam)",
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
            text="(1) Orgán poskytuje údaje na základe žiadosti do 30 dní.",
            text_hash="d" * 64,
            effective_from=date(2022, 1, 1),
            effective_to=None,
        )
    )
    db_session.commit()
    return instrument, provision


def test_happy_path_applies_amendment_and_builds_package(db_session) -> None:
    _seed_instrument(db_session)
    request = DraftingRequest(
        title="Novela zákona č. 500/2022 Z. z.",
        user_instruction="Doplň oprávnenie získavať údaje z registra X.",
        target_instrument_number="500",
        target_instrument_year=2022,
        target_provision_reference="§ 12",
        amendment_instructions=[
            AmendmentInstruction(
                operation="nahradit", target_text="do 30 dní", new_text="do 15 dní"
            )
        ],
    )
    package = run_legislative_project(request, db_session, FakeLLMProvider(), as_of=date(2024, 1, 1))

    assert "500/2022 Z. z." in package.current_legal_state
    assert package.consolidated_text is not None
    assert "do 15 dní" in package.consolidated_text
    assert "Strojovo vytvorené pracovné konsolidované znenie" in package.consolidated_text
    assert not any(f.severity == "kriticke" for f in package.control_findings)
    assert package.sources and package.sources[0].instrument_full_citation == "500/2022 Z. z."
    assert package.as_of_was_default is False


def test_amendment_conflict_is_flagged_critical_and_text_unchanged(db_session) -> None:
    _seed_instrument(db_session)
    request = DraftingRequest(
        title="Novela zákona č. 500/2022 Z. z.",
        user_instruction="Skráť lehotu na 15 dní.",
        target_instrument_number="500",
        target_instrument_year=2022,
        target_provision_reference="§ 12",
        amendment_instructions=[
            AmendmentInstruction(
                operation="nahradit", target_text="do 90 dní", new_text="do 15 dní"
            )
        ],
    )
    package = run_legislative_project(request, db_session, FakeLLMProvider(), as_of=date(2024, 1, 1))

    critical = [f for f in package.control_findings if f.severity == "kriticke"]
    assert len(critical) == 1
    assert critical[0].check == "amendment_conflict"
    assert "do 30 dní" in package.consolidated_text  # text sa nezmenil pri konflikte
    assert any("manuálnu úpravu" in q for q in package.open_questions)


def test_missing_target_provision_flags_open_question_not_invented_text(db_session) -> None:
    request = DraftingRequest(
        title="Novela neexistujúceho zákona",
        user_instruction="Uprav § 12.",
        target_instrument_number="999",
        target_instrument_year=2099,
        target_provision_reference="§ 12",
    )
    package = run_legislative_project(request, db_session, FakeLLMProvider(), as_of=date(2024, 1, 1))

    assert "[NEOVERENÉ]" in package.current_legal_state
    assert package.consolidated_text is None
    assert any(f.check == "target_provision_not_found" for f in package.control_findings)
    assert any("nevyhnutné manuálne" in q for q in package.open_questions)
    assert package.sources == []


def test_undefined_internal_reference_in_amendment_is_detected(db_session) -> None:
    _seed_instrument(db_session)
    request = DraftingRequest(
        title="Novela s chybným odkazom",
        user_instruction="Doplň odkaz na neexistujúce ustanovenie.",
        target_instrument_number="500",
        target_instrument_year=2022,
        target_provision_reference="§ 12",
        amendment_instructions=[
            AmendmentInstruction(
                operation="doplnit", new_text=" Postup podľa § 99 sa použije primerane."
            )
        ],
    )
    package = run_legislative_project(request, db_session, FakeLLMProvider(), as_of=date(2024, 1, 1))

    assert any(f.check == "internal_reference" and "99" in f.message for f in package.control_findings)


def test_default_as_of_is_flagged() -> None:
    """Bod 3.3 - ak dátum nie je zadaný, systém to musí explicitne uviesť."""
    request = DraftingRequest(
        title="X",
        user_instruction="Y",
        target_instrument_number="500",
        target_instrument_year=2022,
        target_provision_reference="§ 12",
    )
    # Bez seedovania DB - stačí overiť príznak as_of_was_default, nie nález.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        package = run_legislative_project(request, session, FakeLLMProvider())
        assert package.as_of_was_default is True
        assert package.as_of_date == date.today()
    finally:
        session.close()
