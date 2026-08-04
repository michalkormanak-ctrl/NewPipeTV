from pathlib import Path

from pypdf import PdfReader

from app.export.pdf_exporter import to_pdf, to_pdf_bytes
from tests.factories import sample_legislative_package


def test_pdf_bytes_start_with_pdf_magic() -> None:
    content = to_pdf_bytes(sample_legislative_package())
    assert content[:5] == b"%PDF-"


def test_pdf_contains_title_and_sections_text(tmp_path: Path) -> None:
    package = sample_legislative_package()
    output_path = to_pdf(package, tmp_path / "balik.pdf")
    reader = PdfReader(str(output_path))
    full_text = "\n".join(page.extract_text() for page in reader.pages)

    assert "Novela zákona č. 500/2022 Z. z." in full_text
    assert "Strojovo vytvorený pracovný legislatívny materiál" in full_text
    assert "A. Manažérske zhrnutie" in full_text
    assert "§ 99" in full_text
    assert "500/2022 Z. z." in full_text


def test_pdf_renders_slovak_diacritics_correctly(tmp_path: Path) -> None:
    """Regresný test na diakritiku (č/š/ž/ď/ť/ľ/ň/ô/ĺ/ŕ/ä) - vstavané
    reportlab fonty (Helvetica) tieto znaky nesprávne zobrazujú/vynechávajú,
    preto exportér používa balený DejaVu Sans (app/export/fonts/)."""
    package = sample_legislative_package()
    package.executive_summary = "Žiadosť sa týka ľudských práv a slobôd, počítačový útvar, ôsmy ročník."
    output_path = to_pdf(package, tmp_path / "diakritika.pdf")
    reader = PdfReader(str(output_path))
    full_text = "\n".join(page.extract_text() for page in reader.pages)
    assert "Žiadosť sa týka ľudských práv a slobôd" in full_text
    assert "počítačový útvar, ôsmy ročník" in full_text


def test_pdf_omits_empty_optional_sections(tmp_path: Path) -> None:
    package = sample_legislative_package()
    package.paragraph_wording = None
    output_path = to_pdf(package, tmp_path / "balik2.pdf")
    reader = PdfReader(str(output_path))
    full_text = "\n".join(page.extract_text() for page in reader.pages)
    assert "E. Paragrafové znenie" not in full_text
