"""Build full resume plain text for AI services (job-fit evaluation, summary, etc.)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai_service.prompt_formatting import (
    format_bullet_item,
    format_items_for_prompt,
)
from utils.pdf_text import PdfTextExtractionError, extract_text_from_pdf

if TYPE_CHECKING:
    from resume_builder.models import Resume

logger = logging.getLogger(__name__)


def build_resume_text_for_evaluation(resume: "Resume") -> str:
    """
    Full resume text for Gemini job-fit evaluation (parity with admin playground).

    Priority: PDF extract → original_content → structured fields (includes summary).
    """
    return _build_resume_plain_text(resume, exclude_summary_in_structured=False)


def build_resume_text_for_summary(resume: "Resume") -> str:
    """
    Full resume text for AI professional summary (wizard + same sources as job-fit).

    Priority: PDF extract → original_content → structured fields (omits existing summary).
    """
    return _build_resume_plain_text(resume, exclude_summary_in_structured=True)


def _build_resume_plain_text(
    resume: "Resume",
    *,
    exclude_summary_in_structured: bool,
) -> str:
    pdf_text = _extract_text_from_resume_pdf(resume)
    if pdf_text.strip():
        return pdf_text

    original = (resume.original_content or "").strip()
    if original:
        return original

    structured = format_structured_resume_content(
        resume,
        exclude_summary=exclude_summary_in_structured,
    ).strip()
    if structured:
        return structured

    return "No resume content available."


def _extract_text_from_resume_pdf(resume: "Resume") -> str:
    pdf = resume.pdf_file
    if not pdf:
        return ""
    name = (pdf.name or "").lower()
    if not name.endswith(".pdf"):
        return ""

    try:
        with pdf.open("rb") as fp:
            return extract_text_from_pdf(fp)
    except (PdfTextExtractionError, OSError, ValueError) as exc:
        logger.warning(
            "Could not extract PDF text for resume %s: %s",
            resume.pk,
            exc,
        )
        return ""


def format_structured_resume_content(
    resume: "Resume",
    *,
    exclude_summary: bool = False,
) -> str:
    """Format structured resume JSON into readable plain text."""
    content_parts: list[str] = []

    if resume.personal_info:
        personal = resume.personal_info
        content_parts.append("PERSONAL INFORMATION")
        content_parts.append(f"Name: {personal.get('full_name', 'N/A')}")
        content_parts.append(f"Email: {personal.get('email', 'N/A')}")
        content_parts.append(f"Phone: {personal.get('phone', 'N/A')}")
        if personal.get("location"):
            content_parts.append(f"Location: {personal['location']}")
        if personal.get("linkedin"):
            content_parts.append(f"LinkedIn: {personal['linkedin']}")
        if personal.get("github"):
            content_parts.append(f"GitHub: {personal['github']}")
        if personal.get("portfolio"):
            content_parts.append(f"Portfolio: {personal['portfolio']}")
        content_parts.append("")

    if (
        not exclude_summary
        and resume.personal_info
        and resume.personal_info.get("summary")
    ):
        content_parts.append("PROFESSIONAL SUMMARY")
        content_parts.append(resume.personal_info["summary"])
        content_parts.append("")

    if resume.experience:
        content_parts.append("PROFESSIONAL EXPERIENCE")
        for exp in resume.experience:
            content_parts.append(
                f"{exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}"
            )
            date_line = _format_experience_dates(exp)
            if date_line:
                content_parts.append(date_line)
            elif exp.get("duration"):
                content_parts.append(f"Duration: {exp['duration']}")
            if exp.get("description"):
                content_parts.append(f"Description: {exp['description']}")
            if exp.get("achievements"):
                content_parts.append("Key Achievements:")
                for achievement in exp["achievements"]:
                    content_parts.append(f"• {format_bullet_item(achievement)}")
            content_parts.append("")

    if resume.education:
        content_parts.append("EDUCATION")
        for edu in resume.education:
            content_parts.append(
                f"{edu.get('degree', 'N/A')} - {edu.get('institution', 'N/A')}"
            )
            date_line = _format_education_dates(edu)
            if date_line:
                content_parts.append(date_line)
            elif edu.get("year"):
                content_parts.append(f"Year: {edu['year']}")
            if edu.get("gpa"):
                content_parts.append(f"GPA: {edu['gpa']}")
            content_parts.append("")

    if resume.skills:
        content_parts.append("SKILLS")
        for category, skill_list in resume.skills.items():
            if isinstance(skill_list, list):
                content_parts.append(
                    f"{category}: {format_items_for_prompt(skill_list)}"
                )
            else:
                content_parts.append(f"{category}: {skill_list}")
        content_parts.append("")

    if resume.additional:
        content_parts.append("ADDITIONAL INFORMATION")
        for key, value in resume.additional.items():
            if isinstance(value, list):
                content_parts.append(f"{key}: {format_items_for_prompt(value)}")
            else:
                content_parts.append(f"{key}: {value}")
        content_parts.append("")

    return "\n".join(content_parts)


def _format_experience_dates(exp: dict) -> str:
    start = exp.get("start_date") or exp.get("startDate") or ""
    end = exp.get("end_date") or exp.get("endDate") or ""
    if start and end:
        return f"Dates: {start} — {end}"
    if start:
        return f"Dates: {start} — Present"
    return ""


def _format_education_dates(edu: dict) -> str:
    start = edu.get("start_date") or edu.get("startDate") or ""
    end = edu.get("end_date") or edu.get("endDate") or ""
    if start and end:
        return f"Dates: {start} — {end}"
    if start:
        return f"Dates: {start}"
    return ""
