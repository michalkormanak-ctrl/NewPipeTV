import json

from app.export.html_exporter import to_html
from app.export.json_exporter import to_json
from app.export.markdown_exporter import to_markdown
from tests.factories import sample_legislative_package


def test_markdown_contains_all_sections_and_disclaimer() -> None:
    md = to_markdown(sample_legislative_package())
    assert "# Novela zákona č. 500/2022 Z. z." in md
    assert "Strojovo vytvorený pracovný legislatívny materiál" in md
    for heading in ["A. Manažérske zhrnutie", "E. Paragrafové znenie", "J. Kontrolná správa", "K. Otvorené otázky", "L. Zdroje"]:
        assert heading in md
    assert "§ 99" in md
    assert "500/2022 Z. z." in md


def test_markdown_omits_empty_optional_sections() -> None:
    package = sample_legislative_package()
    package.paragraph_wording = None
    md = to_markdown(package)
    assert "E. Paragrafové znenie" not in md


def test_json_roundtrip_preserves_structure() -> None:
    package = sample_legislative_package()
    data = json.loads(to_json(package))
    assert data["title"] == package.title
    assert data["as_of_date"] == "2026-08-04"
    assert len(data["control_findings"]) == 2
    assert "zavazne" in data["findings_by_severity"]
    assert data["findings_by_severity"]["zavazne"][0]["message"] == "Odkaz na § 99 neexistuje."


def test_html_escapes_content_and_includes_disclaimer() -> None:
    package = sample_legislative_package()
    package.executive_summary = "Návrh <script>alert(1)</script> testovací text."
    html = to_html(package)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "disclaimer" in html
    assert "§ 99" in html
