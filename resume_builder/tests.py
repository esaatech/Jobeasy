from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase

from resume_builder.resume_display import augment_resume_dict_for_rendering
from resume_builder.template_registry import (
    GALLERY_SECTION_STUDENTS,
    STUDENT_GALLERY_SECTION_HEADING,
    gallery_section_index_for_template_id,
    get_resume_template_gallery_sections,
)


class NewGradResumeTemplatesRenderTests(SimpleTestCase):
    """Smoke-test HTML for student/new-grad templates (no Playwright required)."""

    def setUp(self):
        self.resume_data = augment_resume_dict_for_rendering(
            {
                "personal_info": {
                    "full_name": "Alex Chen",
                    "title": "New Grad",
                    "email": "alex@example.com",
                    "phone": "555-0100",
                    "location": "Boston, MA",
                    "summary": "<p>Summary</p>",
                },
                "experience": [
                    {
                        "title": "Peer Tutor",
                        "company": "State University",
                        "start_date": "2022-09",
                        "end_date": "2024-05",
                        "description": "<p>Details.</p>",
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "institution": "State University",
                        "start_date": "2020-09",
                        "end_date": "2024-05",
                        "description": "<p>Honors</p>",
                    }
                ],
                "skills": {
                    "technical": ["Python"],
                    "soft": ["Communication"],
                    "languages": ["English"],
                },
                "additional": {
                    "projects": "<p>Capstone</p>",
                    "certifications": "<p>Cert</p>",
                },
            },
            request=None,
        )

    def test_new_grad_templates_render(self):
        for tid in ("new_grad_ats", "new_grad_projects", "new_grad_profile"):
            with self.subTest(template_id=tid):
                html = render_to_string(
                    f"resume_templates/{tid}.html",
                    {"resume_data": self.resume_data},
                )
                self.assertIn(self.resume_data["personal_info"]["full_name"], html)
                self.assertIn(f"{tid}-template", html)


class GallerySectionsTests(TestCase):
    def test_general_subsections_have_headings(self):
        sections = get_resume_template_gallery_sections()
        headings_before_students = [
            s["heading"]
            for s in sections
            if s.get("heading") and s["heading"] != STUDENT_GALLERY_SECTION_HEADING
        ]
        self.assertGreaterEqual(len(headings_before_students), 3)
        self.assertTrue(all(headings_before_students))

    def test_student_templates_grouped(self):
        sections = get_resume_template_gallery_sections()
        student_section = next(
            (
                s
                for s in sections
                if s.get("heading") == STUDENT_GALLERY_SECTION_HEADING
            ),
            None,
        )
        self.assertIsNotNone(student_section)
        ids = {t["id"] for t in student_section["templates"]}
        for tid in ("new_grad_ats", "new_grad_projects", "new_grad_profile"):
            with self.subTest(template_id=tid):
                self.assertIn(tid, ids)
        for t in student_section["templates"]:
            self.assertEqual(t.get("gallery_section"), GALLERY_SECTION_STUDENTS)

    def test_gallery_section_index_matches_template_slide(self):
        sections = get_resume_template_gallery_sections()
        for idx, sec in enumerate(sections):
            for t in sec.get("templates") or []:
                tid = t["id"]
                with self.subTest(template_id=tid):
                    self.assertEqual(
                        gallery_section_index_for_template_id(sections, tid),
                        idx,
                    )
