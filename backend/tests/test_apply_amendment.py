"""Akceptačný test 18.3/6-7: aplikovateľný novelizačný bod a jeho aplikácia
na aktuálne znenie, vrátane povinného označenia konfliktu (sekcia 7,
R3 v docs/risks.md - žiadne tiché preskočenie)."""
from app.consolidation.apply_amendment import AmendmentInstruction, apply_amendment

ORIGINAL = "(1) Orgán vydá rozhodnutie do 30 dní odo dňa doručenia žiadosti."


def test_replace_applies_when_target_found_exactly_once() -> None:
    instruction = AmendmentInstruction(
        operation="nahradit", target_text="30 dní", new_text="60 dní"
    )
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "applied"
    assert "60 dní" in result.resulting_text
    assert "30 dní" not in result.resulting_text


def test_replace_conflicts_when_target_not_found() -> None:
    instruction = AmendmentInstruction(
        operation="nahradit", target_text="90 dní", new_text="60 dní"
    )
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "conflict"
    assert result.resulting_text == ORIGINAL  # text sa nezmenil
    assert "vyžaduje sa manuálna kontrola" in result.note


def test_replace_conflicts_when_target_ambiguous() -> None:
    text = "Lehota je 30 dní. Predĺžená lehota je tiež 30 dní."
    instruction = AmendmentInstruction(operation="nahradit", target_text="30 dní", new_text="60 dní")
    result = apply_amendment(text, instruction)
    assert result.status == "conflict"


def test_delete_applies() -> None:
    instruction = AmendmentInstruction(operation="vypustit", target_text=" odo dňa doručenia žiadosti")
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "applied"
    assert "odo dňa doručenia žiadosti" not in result.resulting_text


def test_insert_after_anchor_applies() -> None:
    instruction = AmendmentInstruction(
        operation="vlozit", anchor_text="30 dní", new_text=", ak osobitný predpis neustanovuje inak"
    )
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "applied"
    assert "30 dní, ak osobitný predpis neustanovuje inak" in result.resulting_text


def test_append_without_anchor() -> None:
    instruction = AmendmentInstruction(operation="doplnit", new_text="(2) Nová veta.")
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "applied"
    assert result.resulting_text.endswith("(2) Nová veta.")


def test_unknown_operation_is_conflict_not_silent_noop() -> None:
    instruction = AmendmentInstruction(operation="nezname", new_text="x")
    result = apply_amendment(ORIGINAL, instruction)
    assert result.status == "conflict"
    assert result.resulting_text == ORIGINAL
