"""Point-in-time modul (sekcia 7). Zisťuje znenie účinné k dátumu, porovnáva
verzie a nachádza novelizujúci predpis. Pracuje nad jednoduchými
dataclass-mi (nie priamo nad ORM), aby bol testovateľný bez DB."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProvisionSnapshot:
    provision_id: str
    label: str
    text: str
    effective_from: date
    effective_to: date | None
    amended_by_instrument: str | None = None
    is_repealed: bool = False


class NoEffectiveVersionError(LookupError):
    """Pre daný dátum neexistuje žiadne účinné znenie (napr. ešte
    neúčinné, alebo predpis/ustanovenie bolo k danému dátumu zrušené)."""


def get_effective_version(
    versions: list[ProvisionSnapshot], as_of: date
) -> ProvisionSnapshot:
    for version in versions:
        if version.effective_from <= as_of and (
            version.effective_to is None or as_of <= version.effective_to
        ):
            return version
    raise NoEffectiveVersionError(
        f"Žiadne znenie nie je účinné k dátumu {as_of.isoformat()}."
    )


@dataclass(frozen=True)
class VersionDiff:
    old_label: str
    new_label: str
    unified_diff: str
    changed: bool
    amending_instrument: str | None


def diff_versions(old: ProvisionSnapshot, new: ProvisionSnapshot) -> VersionDiff:
    diff_lines = list(
        difflib.unified_diff(
            old.text.splitlines(keepends=True),
            new.text.splitlines(keepends=True),
            fromfile=f"{old.label} (od {old.effective_from.isoformat()})",
            tofile=f"{new.label} (od {new.effective_from.isoformat()})",
        )
    )
    return VersionDiff(
        old_label=old.label,
        new_label=new.label,
        unified_diff="".join(diff_lines),
        changed=old.text != new.text,
        amending_instrument=new.amended_by_instrument,
    )


CONSOLIDATION_DISCLAIMER = (
    "Strojovo vytvorené pracovné konsolidované znenie. Pred použitím musí "
    "byť overené oproti oficiálnym zdrojom."
)
