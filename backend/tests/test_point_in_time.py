"""Akceptačné testy 18.3 body 1-3."""
from datetime import date

import pytest

from app.consolidation.point_in_time import (
    NoEffectiveVersionError,
    ProvisionSnapshot,
    diff_versions,
    get_effective_version,
)

V1 = ProvisionSnapshot(
    provision_id="p1",
    label="§ 5",
    text="Pôvodné znenie ustanovenia.",
    effective_from=date(2020, 1, 1),
    effective_to=date(2022, 12, 31),
    amended_by_instrument=None,
)
V2 = ProvisionSnapshot(
    provision_id="p1",
    label="§ 5",
    text="Novelizované znenie ustanovenia platné od roku 2023.",
    effective_from=date(2023, 1, 1),
    effective_to=None,
    amended_by_instrument="zákon č. 100/2022 Z. z.",
)
VERSIONS = [V1, V2]


def test_get_effective_version_before_amendment() -> None:
    """Akceptačný test 18.3/1 a 18.3/13: nájsť znenie účinné k dátumu a
    nedovoliť zámenu historického znenia za aktuálne."""
    result = get_effective_version(VERSIONS, date(2021, 6, 1))
    assert result is V1
    assert result.text == "Pôvodné znenie ustanovenia."


def test_get_effective_version_after_amendment() -> None:
    result = get_effective_version(VERSIONS, date(2024, 1, 1))
    assert result is V2


def test_get_effective_version_no_match_raises() -> None:
    with pytest.raises(NoEffectiveVersionError):
        get_effective_version(VERSIONS, date(2019, 1, 1))


def test_diff_versions_reports_change_and_amending_instrument() -> None:
    """Akceptačný test 18.3/2 a 18.3/3."""
    diff = diff_versions(V1, V2)
    assert diff.changed is True
    assert diff.amending_instrument == "zákon č. 100/2022 Z. z."
    assert "Novelizované znenie" in diff.unified_diff


def test_diff_versions_no_change() -> None:
    diff = diff_versions(V1, V1)
    assert diff.changed is False
