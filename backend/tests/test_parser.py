"""Testy parsera slovenskej právnej štruktúry (sekcia 6.3, akceptačný
kontext pre 18.3). Fixture `synthetic_law_excerpt.txt` je SYNTETICKÝ text
vytvorený len na overenie mechaniky parsera, nie overené znenie reálneho
predpisu (pravidlo 3.1) - pozri hlavičku fixtúry a docs/risks.md R2."""
from pathlib import Path

from app.parser.structure_parser import flatten, parse_instrument_text

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "synthetic_law_excerpt.txt"


def _parse_fixture():
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    return parse_instrument_text(text)


def test_top_level_parts_recognized() -> None:
    roots = _parse_fixture()
    part_labels = [r.label for r in roots if r.unit_type == "cast"]
    assert part_labels == ["PRVÁ", "DRUHÁ"]


def test_paragraf_nested_under_hlava_and_cast() -> None:
    roots = _parse_fixture()
    cast_prva = next(r for r in roots if r.unit_type == "cast" and r.label == "PRVÁ")
    hlava = next(c for c in cast_prva.children if c.unit_type == "hlava")
    assert hlava.label == "I"
    paragraf_1 = next(c for c in hlava.children if c.unit_type == "paragraf")
    assert paragraf_1.label == "1"


def test_odsek_and_pismeno_hierarchy() -> None:
    roots = _parse_fixture()
    flat = flatten(roots)
    paragraf_2 = next(u for u in flat if u.unit_type == "paragraf" and u.label == "2")
    odsek_1 = next(c for c in paragraf_2.children if c.unit_type == "odsek")
    assert odsek_1.label == "1"
    pismena = [c.label for c in odsek_1.children if c.unit_type == "pismeno"]
    assert pismena == ["a", "b", "c"]


def test_nadpis_captured_for_paragraf() -> None:
    roots = _parse_fixture()
    flat = flatten(roots)
    paragraf_1 = next(u for u in flat if u.unit_type == "paragraf" and u.label == "1")
    nadpis = next(c for c in paragraf_1.children if c.unit_type == "nadpis")
    assert nadpis.text == "Predmet zákona"


def test_full_text_reconstruction_nonempty() -> None:
    roots = _parse_fixture()
    flat = flatten(roots)
    odsek_1a = next(
        u
        for u in flat
        if u.unit_type == "pismeno" and u.label == "a"
    )
    assert "legislatívnym procesom" in odsek_1a.text


def test_text_hash_stable_for_same_content() -> None:
    roots1 = _parse_fixture()
    roots2 = _parse_fixture()
    flat1 = {u.hierarchical_path(): u.text_hash() for u in flatten(roots1)}
    flat2 = {u.hierarchical_path(): u.text_hash() for u in flatten(roots2)}
    assert flat1 == flat2


def test_unrecognized_line_is_not_silently_dropped() -> None:
    """Text bez rozpoznaného vzoru sa musí pripojiť k aktuálnemu uzlu, nie
    zahodiť (bod 6.3 - žiadne ticho stratené ustanovenie)."""
    text = (
        "§ 9\nNejaký nadpis\n(1) Prvá veta.\n"
        "Toto je dodatočný neformátovaný text bez vzoru na začiatku riadku."
    )
    roots = parse_instrument_text(text)
    flat = flatten(roots)
    odsek = next(u for u in flat if u.unit_type == "odsek")
    assert "dodatočný neformátovaný text" in odsek.text
