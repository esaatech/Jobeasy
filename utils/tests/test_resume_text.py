import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from resume_builder.models import Resume
from utils.resume_text import build_resume_text_for_evaluation

User = get_user_model()


def _make_pdf(path: Path, line: str) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 700, line)
    c.save()


class BuildResumeTextForEvaluationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="evaluser", password="pass")

    def test_prefers_original_content_over_structured_fields(self):
        resume = Resume.objects.create(
            user=self.user,
            template_id="executive",
            original_content="Full upload text\nFounder 2023-09 — Present\nEsaatechnology",
            personal_info={"full_name": "Jane Doe"},
            experience=[
                {
                    "title": "Developer",
                    "company": "Acme",
                    "start_date": "2020-01",
                    "end_date": "Present",
                }
            ],
        )
        text = build_resume_text_for_evaluation(resume)
        self.assertEqual(text, resume.original_content)
        self.assertNotIn("PROFESSIONAL EXPERIENCE", text)

    def test_extracts_from_stored_pdf_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "resume.pdf"
            _make_pdf(pdf_path, "Stored PDF marker ABC123")
            with pdf_path.open("rb") as fh:
                upload = SimpleUploadedFile(
                    "resume.pdf",
                    fh.read(),
                    content_type="application/pdf",
                )

            resume = Resume.objects.create(
                user=self.user,
                template_id="executive",
                original_content="Should not be used when PDF extracts",
                pdf_file=upload,
            )

        text = build_resume_text_for_evaluation(resume)
        self.assertIn("Stored PDF marker ABC123", text)
        self.assertNotIn("Should not be used when PDF extracts", text)

    def test_falls_back_to_structured_when_no_source_text(self):
        resume = Resume.objects.create(
            user=self.user,
            template_id="executive",
            original_content="",
            personal_info={"full_name": "Jane Doe", "email": "j@example.com"},
            experience=[
                {
                    "title": "Engineer",
                    "company": "Acme",
                    "start_date": "2023-09",
                    "end_date": "Present",
                }
            ],
        )
        text = build_resume_text_for_evaluation(resume)
        self.assertIn("Engineer at Acme", text)
        self.assertIn("Dates: 2023-09 — Present", text)
