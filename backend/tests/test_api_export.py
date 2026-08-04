"""Integračný test /api/v1/export/* endpointov."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_PAYLOAD = {
    "title": "Testovací legislatívny balík",
    "generated_at": "2026-08-04",
    "as_of_date": "2026-08-04",
    "as_of_was_default": True,
    "executive_summary": "Zhrnutie návrhu.",
    "current_legal_state": "§ 5 v súčasnosti upravuje X.",
    "problem_map": "Cieľ: Y.",
    "variants": "Odporúčaný variant: Z.",
    "control_findings": [
        {"check": "internal_reference", "severity": "zavazne", "message": "Chýbajúci odkaz.", "location": "§ 9"}
    ],
    "open_questions": ["Otvorená otázka 1?"],
    "sources": [{"instrument_full_citation": "500/2022 Z. z.", "provision_label": "§ 5"}],
}


def test_export_markdown() -> None:
    response = client.post("/api/v1/export/markdown", json=_PAYLOAD)
    assert response.status_code == 200
    assert "# Testovací legislatívny balík" in response.text
    assert "§ 9" in response.text


def test_export_html() -> None:
    response = client.post("/api/v1/export/html", json=_PAYLOAD)
    assert response.status_code == 200
    assert "<html" in response.text
    assert "Testovací legislatívny balík" in response.text


def test_export_json() -> None:
    response = client.post("/api/v1/export/json", json=_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Testovací legislatívny balík"


def test_export_docx_returns_office_document() -> None:
    response = client.post("/api/v1/export/docx", json=_PAYLOAD)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert response.content[:2] == b"PK"  # DOCX je ZIP kontajner


def test_export_pdf_returns_pdf_document() -> None:
    response = client.post("/api/v1/export/pdf", json=_PAYLOAD)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_export_findings_xlsx_returns_spreadsheet() -> None:
    response = client.post("/api/v1/export/xlsx/findings", json=_PAYLOAD)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content[:2] == b"PK"


def test_export_findings_xlsx_rejects_empty_findings() -> None:
    payload = dict(_PAYLOAD)
    payload["control_findings"] = []
    response = client.post("/api/v1/export/xlsx/findings", json=payload)
    assert response.status_code == 422


_COMMENTS_PAYLOAD = [
    {
        "author": "Ministerstvo financií SR",
        "target_provision_label": "§ 5 ods. 2",
        "comment_type": "zasadna",
        "is_fundamental": True,
        "text": "Navrhujeme predĺžiť lehotu.",
        "proposed_wording": "30 dní sa nahrádza slovami 60 dní.",
        "result": "ciastocne_akceptovana",
    }
]


def test_export_comments_xlsx_returns_spreadsheet() -> None:
    response = client.post("/api/v1/export/xlsx/comments", json=_COMMENTS_PAYLOAD)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content[:2] == b"PK"


def test_export_comments_xlsx_rejects_empty_list() -> None:
    response = client.post("/api/v1/export/xlsx/comments", json=[])
    assert response.status_code == 422
