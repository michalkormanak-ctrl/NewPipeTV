"""Strojová aplikácia novelizačného bodu na aktuálne znenie (sekcia 7, krok 8
zadania). Bod, ktorý nemožno jednoznačne aplikovať, sa VŽDY označí ako
konflikt - nikdy sa ticho nepreskočí (bod 7, R3 v docs/risks.md)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AmendmentInstruction:
    operation: str  # nahradit | vlozit | vypustit | doplnit
    target_text: str | None = None
    anchor_text: str | None = None
    new_text: str | None = None


@dataclass(frozen=True)
class ApplicationResult:
    status: str  # applied | conflict
    resulting_text: str
    note: str


def apply_amendment(current_text: str, instruction: AmendmentInstruction) -> ApplicationResult:
    op = instruction.operation

    if op == "nahradit":
        return _apply_replace(current_text, instruction)
    if op == "vypustit":
        return _apply_delete(current_text, instruction)
    if op == "vlozit":
        return _apply_insert_after_anchor(current_text, instruction)
    if op == "doplnit":
        return _apply_append(current_text, instruction)

    return ApplicationResult(
        status="conflict",
        resulting_text=current_text,
        note=f"Neznámy typ operácie novelizačného bodu: '{op}'.",
    )


def _apply_replace(current_text: str, instruction: AmendmentInstruction) -> ApplicationResult:
    target = instruction.target_text or ""
    count = current_text.count(target)
    if not target or count != 1:
        return ApplicationResult(
            status="conflict",
            resulting_text=current_text,
            note=(
                f"Text na nahradenie sa v ustanovení nenašiel presne raz (nájdených: {count}); "
                "vyžaduje sa manuálna kontrola."
            ),
        )
    new_text = current_text.replace(target, instruction.new_text or "")
    return ApplicationResult(status="applied", resulting_text=new_text, note="")


def _apply_delete(current_text: str, instruction: AmendmentInstruction) -> ApplicationResult:
    target = instruction.target_text or ""
    count = current_text.count(target)
    if not target or count != 1:
        return ApplicationResult(
            status="conflict",
            resulting_text=current_text,
            note=(
                f"Text na vypustenie sa v ustanovení nenašiel presne raz (nájdených: {count}); "
                "vyžaduje sa manuálna kontrola."
            ),
        )
    return ApplicationResult(status="applied", resulting_text=current_text.replace(target, ""), note="")


def _apply_insert_after_anchor(current_text: str, instruction: AmendmentInstruction) -> ApplicationResult:
    anchor = instruction.anchor_text or ""
    count = current_text.count(anchor)
    if not anchor or count != 1:
        return ApplicationResult(
            status="conflict",
            resulting_text=current_text,
            note=(
                f"Kotviaci text pre vloženie sa nenašiel presne raz (nájdených: {count}); "
                "vyžaduje sa manuálna kontrola."
            ),
        )
    index = current_text.index(anchor) + len(anchor)
    new_text = current_text[:index] + (instruction.new_text or "") + current_text[index:]
    return ApplicationResult(status="applied", resulting_text=new_text, note="")


def _apply_append(current_text: str, instruction: AmendmentInstruction) -> ApplicationResult:
    if instruction.anchor_text:
        return _apply_insert_after_anchor(
            current_text,
            AmendmentInstruction(
                operation="vlozit",
                anchor_text=instruction.anchor_text,
                new_text=instruction.new_text,
            ),
        )
    separator = "\n" if current_text and not current_text.endswith("\n") else ""
    return ApplicationResult(
        status="applied",
        resulting_text=current_text + separator + (instruction.new_text or ""),
        note="",
    )
