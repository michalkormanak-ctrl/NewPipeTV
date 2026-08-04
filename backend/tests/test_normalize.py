import pytest

from app.search.normalize import normalize_reference

# Sekcia 9.2 zadania - rôzne zápisy toho istého odkazu musia normalizovať
# na rovnaký kanonický tvar.
EQUIVALENT_PARAGRAF_ODSEK = [
    "§ 31 ods. 2",
    "paragraf 31 odsek 2",
    "ust. § 31/2",
    "§31(2)",
]


@pytest.mark.parametrize("raw", EQUIVALENT_PARAGRAF_ODSEK)
def test_paragraf_odsek_variants_normalize_equally(raw: str) -> None:
    ref = normalize_reference(raw)
    assert ref.unit == "§"
    assert ref.number == "31"
    assert ref.odsek == "2"
    assert ref.canonical() == "§31/ods.2"


def test_clanok_odsek_pismeno() -> None:
    ref = normalize_reference("čl. 6 ods. 1 písm. c)")
    assert ref.unit == "čl."
    assert ref.number == "6"
    assert ref.odsek == "1"
    assert ref.pismeno == "c"


def test_paragraf_odsek_pismeno_bod() -> None:
    ref = normalize_reference("§31 ods. 2 písm. c) bod 3")
    assert (ref.number, ref.odsek, ref.pismeno, ref.bod) == ("31", "2", "c", "3")


def test_instrument_citation_only() -> None:
    ref = normalize_reference("zákon č. 500/2022 Z. z.")
    assert ref.instrument_number == "500"
    assert ref.instrument_year == "2022"
    assert ref.unit is None


def test_combined_provision_and_instrument_reference_no_collision() -> None:
    """Regresný test: kompaktný zápis odseku sa nesmie zamieňať s
    číslo/rok citáciou predpisu (§31/2 vs. 500/2022 Z. z.)."""
    ref = normalize_reference("§ 31 ods. 2 zákona č. 500/2022 Z. z.")
    assert ref.number == "31"
    assert ref.odsek == "2"
    assert ref.instrument_number == "500"
    assert ref.instrument_year == "2022"


def test_no_match_returns_empty_reference() -> None:
    ref = normalize_reference("všeobecný text bez odkazu")
    assert ref.unit is None
    assert ref.instrument_number is None
