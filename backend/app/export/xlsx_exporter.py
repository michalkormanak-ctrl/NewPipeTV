"""XLSX export pre pripomienky a kontrolné tabuľky (sekcia 12, 15 zadania)."""
from __future__ import annotations

import io
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from app.export.package import CommentExportRow, SEVERITY_LABELS, LegislativePackage
from app.validators.legislative import ValidationFinding

_FINDINGS_HEADER = ["Závažnosť", "Kontrola", "Miesto", "Zistenie", "Odporúčanie", "Stav"]
_COMMENTS_HEADER = [
    "Autor",
    "Dotknuté ustanovenie",
    "Typ",
    "Zásadná",
    "Text pripomienky",
    "Navrhované znenie",
    "Odôvodnenie",
    "Tematická kategória",
    "Právny argument",
    "Výsledok",
    "Spôsob zapracovania",
    "Konečné znenie",
]


def _write_header(sheet: Worksheet, header: list[str]) -> None:
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)


def build_findings_workbook(findings: list[ValidationFinding]) -> Workbook:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Kontrolná správa"
    _write_header(sheet, _FINDINGS_HEADER)
    for finding in findings:
        sheet.append(
            [
                SEVERITY_LABELS.get(finding.severity, finding.severity),
                finding.check,
                finding.location or "",
                finding.message,
                "",
                "open",
            ]
        )
    return workbook


def to_findings_xlsx(package: LegislativePackage, path: str | Path) -> Path:
    workbook = build_findings_workbook(package.control_findings)
    output_path = Path(path)
    workbook.save(output_path)
    return output_path


def to_findings_xlsx_bytes(package: LegislativePackage) -> bytes:
    buffer = io.BytesIO()
    build_findings_workbook(package.control_findings).save(buffer)
    return buffer.getvalue()


def build_comments_workbook(comments: list[CommentExportRow]) -> Workbook:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Pripomienky"
    _write_header(sheet, _COMMENTS_HEADER)
    for comment in comments:
        sheet.append(
            [
                comment.author,
                comment.target_provision_label or "",
                comment.comment_type,
                "áno" if comment.is_fundamental else "nie",
                comment.text,
                comment.proposed_wording or "",
                comment.justification or "",
                comment.thematic_category or "",
                comment.legal_argument or "",
                comment.result or "",
                comment.resolution_method or "",
                comment.final_wording or "",
            ]
        )
    return workbook


def to_comments_xlsx(comments: list[CommentExportRow], path: str | Path) -> Path:
    workbook = build_comments_workbook(comments)
    output_path = Path(path)
    workbook.save(output_path)
    return output_path
