from __future__ import annotations

from html import escape

from app.export.package import SECTION_TITLES, SEVERITY_LABELS, SEVERITY_ORDER, LegislativePackage


def _text_to_html(text: str) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(
        f"<p>{escape(p).replace(chr(10), '<br>')}</p>" for p in paragraphs
    ) or f"<p>{escape(text)}</p>"


def to_html(package: LegislativePackage) -> str:
    parts: list[str] = [
        "<!doctype html><html lang=\"sk\"><head><meta charset=\"utf-8\">",
        f"<title>{escape(package.title)}</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;}"
        ".disclaimer{background:#f8d7da;padding:0.75rem;border-radius:6px;}"
        "table{border-collapse:collapse;width:100%;}td,th{border:1px solid #ccc;padding:0.4rem;text-align:left;}"
        "</style></head><body>",
        f"<h1>{escape(package.title)}</h1>",
        f"<p class=\"disclaimer\">{escape(package.disclaimer)}</p>",
        f"<p><em>Vytvorené: {package.generated_at.isoformat()} · "
        f"Právny stav posudzovaný k: {package.as_of_date.isoformat()}"
        + (" (predvolený)" if package.as_of_was_default else "")
        + "</em></p>",
    ]

    for attr, heading in SECTION_TITLES:
        value = getattr(package, attr)
        if not value:
            continue
        parts.append(f"<h2>{escape(heading)}</h2>")
        parts.append(_text_to_html(value))

    parts.append("<h2>J. Kontrolná správa</h2>")
    grouped = package.findings_by_severity()
    any_findings = False
    for severity in SEVERITY_ORDER:
        findings = grouped.get(severity, [])
        if not findings:
            continue
        any_findings = True
        parts.append(f"<h3>{escape(SEVERITY_LABELS[severity])}</h3>")
        parts.append("<table><tr><th>Kontrola</th><th>Miesto</th><th>Zistenie</th></tr>")
        for finding in findings:
            parts.append(
                f"<tr><td>{escape(finding.check)}</td>"
                f"<td>{escape(finding.location or '')}</td>"
                f"<td>{escape(finding.message)}</td></tr>"
            )
        parts.append("</table>")
    if not any_findings:
        parts.append("<p>Žiadne nálezy.</p>")

    parts.append("<h2>K. Otvorené otázky</h2>")
    if package.open_questions:
        parts.append("<ul>" + "".join(f"<li>{escape(q)}</li>" for q in package.open_questions) + "</ul>")
    else:
        parts.append("<p>Žiadne otvorené otázky vyžadujúce rozhodnutie človeka.</p>")

    parts.append("<h2>L. Zdroje</h2>")
    if package.sources:
        parts.append("<ul>")
        for source in package.sources:
            provision = f", {source.provision_label}" if source.provision_label else ""
            url = f" — <a href=\"{escape(source.source_url)}\">{escape(source.source_url)}</a>" if source.source_url else ""
            parts.append(f"<li>{escape(source.instrument_full_citation)}{escape(provision)}{url}</li>")
        parts.append("</ul>")
    else:
        parts.append("<p>Žiadne zdroje neboli priložené.</p>")

    parts.append("</body></html>")
    return "".join(parts)
