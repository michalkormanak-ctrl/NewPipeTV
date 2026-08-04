"""Export legislatívneho balíka (sekcia 14/15 zadania) do viacerých formátov.

Poznámka: tento endpoint exportuje balík, ktorý klient (UI alebo iný
backend proces) zostavil - neorchestruje samotné generovanie obsahu balíka
(to vyžaduje LLM prístup, mimo pilotu, viď docs/known-limitations.md)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from app.export.docx_exporter import to_docx_bytes
from app.export.html_exporter import to_html
from app.export.json_exporter import to_json
from app.export.markdown_exporter import to_markdown
from app.export.xlsx_exporter import to_comments_xlsx_bytes, to_findings_xlsx_bytes
from app.schemas.export import CommentExportRowIn, LegislativePackageIn

router = APIRouter(prefix="/api/v1/export", tags=["export"])

_DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/markdown", response_class=PlainTextResponse)
def export_markdown(package_in: LegislativePackageIn) -> str:
    return to_markdown(package_in.to_dataclass())


@router.post("/html", response_class=HTMLResponse)
def export_html(package_in: LegislativePackageIn) -> str:
    return to_html(package_in.to_dataclass())


@router.post("/json", response_class=PlainTextResponse)
def export_json(package_in: LegislativePackageIn) -> Response:
    return Response(content=to_json(package_in.to_dataclass()), media_type="application/json")


@router.post("/docx")
def export_docx(package_in: LegislativePackageIn) -> Response:
    content = to_docx_bytes(package_in.to_dataclass())
    return Response(
        content=content,
        media_type=_DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="legislativny-material.docx"'},
    )


@router.post("/xlsx/findings")
def export_findings_xlsx(package_in: LegislativePackageIn) -> Response:
    package = package_in.to_dataclass()
    if not package.control_findings:
        raise HTTPException(status_code=422, detail="Balík neobsahuje žiadne nálezy na export.")
    content = to_findings_xlsx_bytes(package)
    return Response(
        content=content,
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="kontrolna-sprava.xlsx"'},
    )


@router.post("/xlsx/comments")
def export_comments_xlsx(comments_in: list[CommentExportRowIn]) -> Response:
    """Export pripomienok z legislatívneho procesu (sekcia 12 zadania)."""
    if not comments_in:
        raise HTTPException(status_code=422, detail="Zoznam pripomienok je prázdny.")
    content = to_comments_xlsx_bytes([c.to_dataclass() for c in comments_in])
    return Response(
        content=content,
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="pripomienky.xlsx"'},
    )
