"""Akceptačné testy 18.3 body 8, 9, 12."""
from app.validators.legislative import (
    check_internal_references,
    check_missing_data_markers,
    check_undefined_terms,
)


def test_detects_nonexistent_internal_reference() -> None:
    """18.3/8: odhaliť neexistujúci vnútorný odkaz."""
    text = "Postup podľa § 5 ods. 1 sa použije primerane aj podľa § 99."
    findings = check_internal_references(text, known_paragraf_labels={"5"})
    assert any("99" in f.message for f in findings)
    assert not any("5" == f.location for f in findings)


def test_no_finding_when_all_references_exist() -> None:
    text = "Postup podľa § 5 sa použije primerane."
    findings = check_internal_references(text, known_paragraf_labels={"5"})
    assert findings == []


def test_detects_undefined_term() -> None:
    """18.3/9: odhaliť nedefinovaný pojem."""
    text = "Žiadateľ je povinný predložiť doklad o oprávnenej osobe."
    findings = check_undefined_terms(
        text, defined_terms={"žiadateľ"}, candidate_terms={"žiadateľ", "oprávnenej osobe"}
    )
    assert len(findings) == 1
    assert findings[0].location == "oprávnenej osobe"


def test_missing_data_marker_is_flagged_not_invented() -> None:
    """18.3/12: chýbajúce údaje musia byť označené, nie vymyslené."""
    text = "Vplyv na rozpočet verejnej správy: [DOPLNIŤ ODHAD ROZPOČTOVÉHO VPLYVU]"
    findings = check_missing_data_markers(text)
    assert len(findings) == 1
    assert findings[0].check == "missing_data_marker_present"
