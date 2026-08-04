"""Test ingestora nad fixture HTML (ADR-0003) - bez siete.

Reálny sieťový prístup na slov-lex.sk bol v tomto vývojovom sedení
zablokovaný egress politikou (docs/00-source-map.md, docs/risks.md R2),
preto testy overujú parsovaciu logiku nad uloženou fixture stránkou, nie
proti živému webu. Selektory sa musia doladiť/potvrdiť pred produkciou."""
import hashlib
from pathlib import Path

from app.ingestion.base import FetchedDocument
from app.ingestion.slovlex import parse_slovlex_html

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "slovlex_sample.html"


def _load_fixture() -> FetchedDocument:
    content = FIXTURE_PATH.read_bytes()
    return FetchedDocument(
        source_url="https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2015/400/",
        content=content,
        mime_type="text/html; charset=utf-8",
        status_code=200,
    )


def test_parses_title_and_citation() -> None:
    result = parse_slovlex_html(_load_fixture())
    assert "právnych predpisov" in result.title
    assert result.full_citation == "400/2015 Z. z."


def test_extracts_plain_text_content() -> None:
    result = parse_slovlex_html(_load_fixture())
    assert "§ 1" in result.plain_text
    assert "legislatívnym procesom" in result.plain_text


def test_integrity_hash_matches_content() -> None:
    """Bod 5.3: SHA-256 sa musí evidovať a musí zodpovedať stiahnutému obsahu."""
    fetched = _load_fixture()
    expected = hashlib.sha256(fetched.content).hexdigest()
    result = parse_slovlex_html(fetched)
    assert result.sha256 == expected
    assert result.size_bytes == len(fetched.content)


def test_unknown_structure_flagged_not_invented() -> None:
    """Ak stránka nemá rozpoznateľný titulok, ingestor si názov nevymyslí,
    ale explicitne označí potrebu manuálnej kontroly (pravidlo 3.1)."""
    empty_doc = FetchedDocument(
        source_url="https://www.slov-lex.sk/x",
        content=b"<html><body><p>bez ocakavanej struktury</p></body></html>",
        mime_type="text/html",
        status_code=200,
    )
    result = parse_slovlex_html(empty_doc)
    assert "vyžaduje manuálnu kontrolu" in result.title
