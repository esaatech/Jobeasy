import tempfile
import unittest
from pathlib import Path

from django.test import SimpleTestCase
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from utils.pdf_text import PdfTextExtractionError, extract_text_from_pdf

# Known resume PDF used for integration checks when present locally.
SAMPLE_RESUME_PDF = Path("/Users/joelivongbe/Downloads/resume_4 (2).pdf")
EXPECTED_RESUME_SNIPPETS = (
    "Joel Ivongbe",
    "Founder, Full-Stack Engineer & AI Engineer",
    "Esaatechnology",
    "2023-09",
    "PROFESSIONAL EXPERIENCE",
)


def _write_test_pdf(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    c.save()


class ExtractTextFromPdfTests(SimpleTestCase):
    def test_extracts_all_pages_from_generated_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "two_page.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            c.drawString(72, 700, "Page one line alpha")
            c.drawString(72, 684, "Page one line beta")
            c.showPage()
            c.drawString(72, 700, "Page two line gamma")
            c.save()

            text = extract_text_from_pdf(pdf_path)

        self.assertIn("Page one line alpha", text)
        self.assertIn("Page one line beta", text)
        self.assertIn("Page two line gamma", text)

    def test_extracts_from_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "single.pdf"
            _write_test_pdf(pdf_path, ["Bytes source marker XYZ"])

            data = pdf_path.read_bytes()
            text = extract_text_from_pdf(data)

        self.assertIn("Bytes source marker XYZ", text)

    def test_raises_when_file_missing(self):
        with self.assertRaises(PdfTextExtractionError) as ctx:
            extract_text_from_pdf("/nonexistent/resume.pdf")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_raises_when_pdf_has_no_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "empty.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            c.showPage()
            c.save()

            with self.assertRaises(PdfTextExtractionError) as ctx:
                extract_text_from_pdf(pdf_path)
            self.assertIn("no extractable text", str(ctx.exception).lower())


@unittest.skipUnless(
    SAMPLE_RESUME_PDF.is_file(),
    f"Sample resume not found at {SAMPLE_RESUME_PDF}",
)
class ExtractTextFromRealResumePdfTests(SimpleTestCase):
    """Integration test against the user's resume PDF when available locally."""

    def test_extracts_full_resume_content(self):
        text = extract_text_from_pdf(SAMPLE_RESUME_PDF)

        self.assertGreater(len(text), 5000, "Expected substantial text from resume PDF")
        for snippet in EXPECTED_RESUME_SNIPPETS:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)
