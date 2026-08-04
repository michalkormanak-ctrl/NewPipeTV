"""Rozklad slovenského právneho textu na štrukturálne jednotky (sekcia 6.3).

Vstup je čistý text (už extrahovaný z HTML/PDF vrstvou parsovania).
Výstup je strom ParsedUnit uzlov, ktorý sa následne mapuje na entity
`Provision`/`ProvisionVersion` (docs/data-model.md).

Parser je zámerne konzervatívny: text, ktorý sa nedá jednoznačne priradiť
k žiadnemu vzoru, sa nezahodí, ale pripojí k najbližšiemu otvorenému uzlu a
uzol nesúci neistotu sa označí `needs_review=True` (bod 6.3 + R8 v
docs/risks.md), aby analytik vedel, že treba manuálnu kontrolu.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

_ROMAN_OR_WORD = r"[A-ZÁČĎÉÍĹĽŇÓŔŠŤÚÝŽ0-9]+"

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cast", re.compile(rf"^\s*ČASŤ\s+({_ROMAN_OR_WORD})\s*$")),
    ("hlava", re.compile(rf"^\s*HLAVA\s+({_ROMAN_OR_WORD})\s*$")),
    ("diel", re.compile(rf"^\s*DIEL\s+({_ROMAN_OR_WORD})\s*$")),
    ("oddiel", re.compile(rf"^\s*[Oo]ddiel\s+({_ROMAN_OR_WORD})\s*$")),
    ("priloha", re.compile(r"^\s*Príloha\s+č\.?\s*(\d+[a-z]?)\s*$", re.IGNORECASE)),
    ("paragraf", re.compile(r"^\s*§\s*(\d+[a-z]?)\s*$")),
    ("odsek", re.compile(r"^\s*\((\d+)\)\s*(.*)$")),
    ("pismeno", re.compile(r"^\s*([a-záäčďéíľĺňóôŕšťúýž])\)\s*(.*)$")),
    ("bod", re.compile(r"^\s*(\d+)\.\s+(.*)$")),
]

_RANK = {
    "cast": 1,
    "hlava": 2,
    "diel": 3,
    "oddiel": 4,
    "priloha": 4,
    "paragraf": 5,
    "odsek": 6,
    "pismeno": 7,
    "bod": 8,
}


@dataclass
class ParsedUnit:
    unit_type: str
    label: str
    order_index: int
    text: str = ""
    children: list["ParsedUnit"] = field(default_factory=list)
    needs_review: bool = False

    def text_hash(self) -> str:
        return hashlib.sha256(self.full_text().encode("utf-8")).hexdigest()

    def full_text(self) -> str:
        parts = [self.text] if self.text else []
        for child in self.children:
            parts.append(child.full_text())
        return "\n".join(p for p in parts if p).strip()

    def hierarchical_path(self, parent_path: str = "") -> str:
        segment = f"{self.unit_type}:{self.label}"
        return f"{parent_path}/{segment}" if parent_path else segment

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def _match_line(line: str) -> tuple[str, str, str] | None:
    for unit_type, pattern in _PATTERNS:
        m = pattern.match(line)
        if m:
            groups = m.groups()
            label = groups[0]
            inline_text = groups[1] if len(groups) > 1 else ""
            return unit_type, label, inline_text or ""
    return None


def parse_instrument_text(text: str) -> list[ParsedUnit]:
    """Rozloží text predpisu na strom ParsedUnit. Nikdy nevyhodí výnimku na
    neznámy vzor - neznáme riadky sa pripoja ako text k aktuálnemu uzlu."""

    roots: list[ParsedUnit] = []
    stack: list[ParsedUnit] = []
    order_counters: dict[int, int] = {}

    def next_order(rank: int) -> int:
        order_counters[rank] = order_counters.get(rank, 0) + 1
        return order_counters[rank]

    pending_heading_for: ParsedUnit | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        matched = _match_line(line)
        if matched is None:
            # Riadok bez rozpoznaného vzoru: heuristika pre nadpis ustanovenia
            # - krátky riadok hneď po "§ N" a pred prvým odsekom.
            if (
                pending_heading_for is not None
                and not pending_heading_for.children
                and len(line.strip()) < 200
            ):
                heading = ParsedUnit(
                    unit_type="nadpis",
                    label="nadpis",
                    order_index=0,
                    text=line.strip(),
                )
                pending_heading_for.children.append(heading)
                continue
            if stack:
                stack[-1].text = (stack[-1].text + "\n" + line.strip()).strip()
            else:
                # Text pred prvou rozpoznanou štruktúrou (napr. preambula).
                if not roots or roots[-1].unit_type != "preambula":
                    roots.append(ParsedUnit(unit_type="preambula", label="", order_index=0))
                roots[-1].text = (roots[-1].text + "\n" + line.strip()).strip()
            continue

        unit_type, label, inline_text = matched
        rank = _RANK[unit_type]

        while stack and _RANK[stack[-1].unit_type] >= rank:
            finished = stack.pop()
            if finished is pending_heading_for:
                pending_heading_for = None

        node = ParsedUnit(
            unit_type=unit_type,
            label=label,
            order_index=next_order(rank),
            text=inline_text,
        )

        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)

        stack.append(node)
        if unit_type == "paragraf":
            pending_heading_for = node
        elif pending_heading_for is not None and unit_type != "nadpis":
            pending_heading_for = None

    return roots


def flatten(roots: list[ParsedUnit]) -> list[ParsedUnit]:
    flat: list[ParsedUnit] = []
    for root in roots:
        flat.extend(root.walk())
    return flat
