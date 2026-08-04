"""Akceptačný test 18.3/4: nájsť súvisiace definície pojmu v iných zákonoch."""
from datetime import date

from sqlalchemy import select

from app.models.legal import LegalInstrument
from app.models.provisions import Provision, TermDefinition


def _seed_instrument(db_session, number: str, title: str) -> LegalInstrument:
    instrument = LegalInstrument(
        number=number,
        year=2015,
        full_citation=f"{number}/2015 Z. z.",
        title=title,
        instrument_type="zakon",
        legal_force="zakon",
        issuing_authority="Národná rada SR",
        status="ucinny",
        source="slov-lex",
    )
    db_session.add(instrument)
    db_session.flush()
    return instrument


def test_finds_definitions_of_same_term_across_two_instruments(db_session) -> None:
    instrument_a = _seed_instrument(db_session, "400", "Zákon A (syntetický testovací záznam)")
    instrument_b = _seed_instrument(db_session, "215", "Zákon B (syntetický testovací záznam)")

    provision_a = Provision(
        instrument_id=instrument_a.id,
        unit_type="paragraf",
        order_index=1,
        label="§2",
        hierarchical_path="paragraf:2",
    )
    provision_b = Provision(
        instrument_id=instrument_b.id,
        unit_type="paragraf",
        order_index=1,
        label="§3",
        hierarchical_path="paragraf:3",
    )
    db_session.add_all([provision_a, provision_b])
    db_session.flush()

    db_session.add_all(
        [
            TermDefinition(
                term="gestor",
                defining_provision_id=provision_a.id,
                definition_text="Gestorom sa na účely zákona A rozumie ústredný orgán štátnej správy.",
                effective_from=date(2015, 1, 1),
            ),
            TermDefinition(
                term="gestor",
                defining_provision_id=provision_b.id,
                definition_text="Gestorom sa na účely zákona B rozumie orgán zodpovedný za register.",
                effective_from=date(2015, 1, 1),
            ),
        ]
    )
    db_session.commit()

    results = db_session.execute(
        select(TermDefinition).where(TermDefinition.term == "gestor")
    ).scalars().all()

    assert len(results) == 2
    defining_provision_ids = {d.defining_provision_id for d in results}
    assert defining_provision_ids == {provision_a.id, provision_b.id}
