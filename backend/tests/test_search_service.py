"""Akceptačné testy 18.3/5 a 18.3/13 (bez zámeny historického znenia)."""
from datetime import date

from app.models.legal import LegalInstrument
from app.models.provisions import Provision, ProvisionVersion
from app.search.normalize import normalize_reference
from app.search.service import search, search_exact


def _seed(db_session):
    instrument = LegalInstrument(
        number="400",
        year=2015,
        full_citation="400/2015 Z. z.",
        title="Zákon o tvorbe právnych predpisov (syntetický testovací záznam)",
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
        label="§5",
        hierarchical_path="paragraf:5",
    )
    db_session.add(provision)
    db_session.flush()

    old_version = ProvisionVersion(
        provision_id=provision.id,
        text="Staré znenie účinné do konca roku 2022.",
        text_hash="a" * 64,
        effective_from=date(2020, 1, 1),
        effective_to=date(2022, 12, 31),
    )
    new_version = ProvisionVersion(
        provision_id=provision.id,
        text="Nové znenie účinné od roku 2023.",
        text_hash="b" * 64,
        effective_from=date(2023, 1, 1),
        effective_to=None,
    )
    db_session.add_all([old_version, new_version])
    db_session.commit()
    return instrument, provision


def test_search_exact_returns_version_effective_at_given_date(db_session) -> None:
    _seed(db_session)
    ref = normalize_reference("§ 5")
    results = search_exact(db_session, ref, as_of=date(2021, 6, 1))
    assert len(results) == 1
    assert results[0].text == "Staré znenie účinné do konca roku 2022."


def test_search_exact_does_not_return_historical_version_as_current(db_session) -> None:
    """18.3/13: nesmie sa zameniť historické znenie za aktuálne."""
    _seed(db_session)
    ref = normalize_reference("§ 5")
    results = search_exact(db_session, ref, as_of=date(2024, 1, 1))
    assert len(results) == 1
    assert results[0].text == "Nové znenie účinné od roku 2023."


def test_search_flags_when_as_of_date_was_defaulted(db_session) -> None:
    """Bod 3.3: ak dátum nie je zadaný, systém musí explicitne uviesť, že
    použil aktuálny dátum."""
    _seed(db_session)
    _, effective_as_of, used_default = search(db_session, "§ 5")
    assert used_default is True
    assert effective_as_of == date.today()


def test_search_exact_takes_precedence_over_fulltext(db_session) -> None:
    """Bod 9.1: presná zhoda identifikátora má prednosť."""
    _seed(db_session)
    results, _, _ = search(db_session, "§ 5", as_of=date(2024, 1, 1))
    assert len(results) == 1
    assert results[0].provision_label == "§5"
