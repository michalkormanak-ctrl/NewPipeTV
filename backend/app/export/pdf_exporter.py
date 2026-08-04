"""PDF export (sekcia 15 zadania).

Používa balený DejaVu Sans font (`app/export/fonts/`, licencia v
`fonts/LICENSE`), aby PDF správne zobrazoval slovenskú diakritiku (č, š,
ž, ď, ť, ľ, ň, ô, ĺ, ŕ, ä) nezávisle od fontov nainštalovaných na
hostiteľskom systéme - vstavané fonty reportlab (Helvetica) tieto znaky
nepodporujú."""
from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.export.package import SECTION_TITLES, SEVERITY_LABELS, SEVERITY_ORDER, LegislativePackage

_FONTS_DIR = Path(__file__).parent / "fonts"
_FONT_REGULAR = "DejaVuSans"
_FONT_BOLD = "DejaVuSans-Bold"
_fonts_registered = False


def _ensure_fonts_registered() -> None:
    global _fonts_registered
    if _fonts_registered:
        return
    pdfmetrics.registerFont(TTFont(_FONT_REGULAR, str(_FONTS_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(_FONTS_DIR / "DejaVuSans-Bold.ttf")))
    _fonts_registered = True


def _styles() -> dict[str, ParagraphStyle]:
    _ensure_fonts_registered()
    return {
        "title": ParagraphStyle("title", fontName=_FONT_BOLD, fontSize=16, spaceAfter=12),
        "h1": ParagraphStyle("h1", fontName=_FONT_BOLD, fontSize=13, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName=_FONT_BOLD, fontSize=11, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", fontName=_FONT_REGULAR, fontSize=10, spaceAfter=4, leading=14),
        "disclaimer": ParagraphStyle(
            "disclaimer", fontName=_FONT_BOLD, fontSize=9, textColor=colors.HexColor("#8a1f11"),
            spaceAfter=10, leading=13,
        ),
        "meta": ParagraphStyle("meta", fontName=_FONT_REGULAR, fontSize=8, textColor=colors.grey, spaceAfter=10),
    }


def _table(rows: list[list[str]], font: str) -> Table:
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_pdf_flowables(package: LegislativePackage) -> list:
    styles = _styles()
    story: list = [
        Paragraph(package.title, styles["title"]),
        Paragraph(package.disclaimer, styles["disclaimer"]),
        Paragraph(
            f"Vytvorené: {package.generated_at.isoformat()} · "
            f"Právny stav posudzovaný k: {package.as_of_date.isoformat()}"
            + (" (predvolený)" if package.as_of_was_default else ""),
            styles["meta"],
        ),
    ]

    for attr, heading in SECTION_TITLES:
        value = getattr(package, attr)
        if not value:
            continue
        story.append(Paragraph(heading, styles["h1"]))
        for line in value.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["body"]))

    story.append(Paragraph("J. Kontrolná správa", styles["h1"]))
    grouped = package.findings_by_severity()
    any_findings = False
    for severity in SEVERITY_ORDER:
        findings = grouped.get(severity, [])
        if not findings:
            continue
        any_findings = True
        story.append(Paragraph(SEVERITY_LABELS[severity], styles["h2"]))
        rows = [["Kontrola", "Miesto", "Zistenie"]]
        for finding in findings:
            rows.append([finding.check, finding.location or "", finding.message])
        story.append(_table(rows, _FONT_REGULAR))
        story.append(Spacer(1, 6))
    if not any_findings:
        story.append(Paragraph("Žiadne nálezy.", styles["body"]))

    story.append(Paragraph("K. Otvorené otázky", styles["h1"]))
    if package.open_questions:
        for question in package.open_questions:
            story.append(Paragraph(f"• {question}", styles["body"]))
    else:
        story.append(Paragraph("Žiadne otvorené otázky vyžadujúce rozhodnutie človeka.", styles["body"]))

    story.append(Paragraph("L. Zdroje", styles["h1"]))
    if package.sources:
        rows = [["Predpis", "Ustanovenie", "Zdroj"]]
        for source in package.sources:
            rows.append([source.instrument_full_citation, source.provision_label or "", source.source_url or ""])
        story.append(_table(rows, _FONT_REGULAR))
    else:
        story.append(Paragraph("Žiadne zdroje neboli priložené.", styles["body"]))

    return story


def to_pdf_bytes(package: LegislativePackage) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm
    )
    document.build(build_pdf_flowables(package))
    return buffer.getvalue()


def to_pdf(package: LegislativePackage, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_bytes(to_pdf_bytes(package))
    return output_path
