from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.consolidation.apply_amendment import AmendmentInstruction
from app.generator.legislative_project import DraftingRequest


class AmendmentInstructionIn(BaseModel):
    operation: str
    target_text: str | None = None
    anchor_text: str | None = None
    new_text: str | None = None

    def to_dataclass(self) -> AmendmentInstruction:
        return AmendmentInstruction(**self.model_dump())


class DraftingRequestIn(BaseModel):
    title: str
    user_instruction: str
    target_instrument_number: str
    target_instrument_year: int
    target_provision_reference: str
    amendment_instructions: list[AmendmentInstructionIn] = []
    working_assumptions: list[str] = []
    requested_effective_date: date | None = None
    as_of: date | None = None

    def to_dataclass(self) -> DraftingRequest:
        return DraftingRequest(
            title=self.title,
            user_instruction=self.user_instruction,
            target_instrument_number=self.target_instrument_number,
            target_instrument_year=self.target_instrument_year,
            target_provision_reference=self.target_provision_reference,
            amendment_instructions=[a.to_dataclass() for a in self.amendment_instructions],
            working_assumptions=self.working_assumptions,
            requested_effective_date=self.requested_effective_date,
        )


class FreeTextInstructionIn(BaseModel):
    """Vstup bližší k reálnemu použitiu - "jednoduchý pokyn v prirodzenom
    jazyku" (bod 2 zadania). Interpretácia je heuristická (bez LLM), pozri
    app/generator/instruction_interpreter.py."""

    instruction: str
    title: str | None = None
    as_of: date | None = None
    amendment_instructions: list[AmendmentInstructionIn] = []
