from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from typing import Any

from app.export.package import LegislativePackage


def _json_default(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Nie je možné serializovať typ {type(value)!r}")


def to_dict(package: LegislativePackage) -> dict:
    data = asdict(package)
    data["findings_by_severity"] = {
        severity: [asdict(f) for f in findings]
        for severity, findings in package.findings_by_severity().items()
    }
    return data


def to_json(package: LegislativePackage) -> str:
    return json.dumps(to_dict(package), ensure_ascii=False, indent=2, default=_json_default)
