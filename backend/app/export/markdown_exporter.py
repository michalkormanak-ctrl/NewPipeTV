from __future__ import annotations

from app.export.package import SECTION_TITLES, SEVERITY_LABELS, SEVERITY_ORDER, LegislativePackage


def to_markdown(package: LegislativePackage) -> str:
    lines: list[str] = [f"# {package.title}", ""]
    lines.append(f"> {package.disclaimer}")
    lines.append("")
    lines.append(
        f"Vytvorené: {package.generated_at.isoformat()} · "
        f"Právny stav posudzovaný k: {package.as_of_date.isoformat()}"
        + (" (predvolený - dátum nebol zadaný)" if package.as_of_was_default else "")
    )
    lines.append("")

    for attr, heading in SECTION_TITLES:
        value = getattr(package, attr)
        if not value:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(value)
        lines.append("")

    lines.append("## J. Kontrolná správa")
    lines.append("")
    grouped = package.findings_by_severity()
    any_findings = False
    for severity in SEVERITY_ORDER:
        findings = grouped.get(severity, [])
        if not findings:
            continue
        any_findings = True
        lines.append(f"### {SEVERITY_LABELS[severity]}")
        for finding in findings:
            location = f" (`{finding.location}`)" if finding.location else ""
            lines.append(f"- **{finding.check}**{location}: {finding.message}")
        lines.append("")
    if not any_findings:
        lines.append("Žiadne nálezy.")
        lines.append("")

    lines.append("## K. Otvorené otázky")
    lines.append("")
    if package.open_questions:
        for question in package.open_questions:
            lines.append(f"- {question}")
    else:
        lines.append("Žiadne otvorené otázky vyžadujúce rozhodnutie človeka.")
    lines.append("")

    lines.append("## L. Zdroje")
    lines.append("")
    if package.sources:
        for source in package.sources:
            provision = f", {source.provision_label}" if source.provision_label else ""
            url = f" — {source.source_url}" if source.source_url else ""
            note = f" _{source.note}_" if source.note else ""
            lines.append(f"- {source.instrument_full_citation}{provision}{url}{note}")
    else:
        lines.append("Žiadne zdroje neboli priložené.")
    lines.append("")

    return "\n".join(lines)
