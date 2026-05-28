# AI Service Package — avoid importing DB-backed modules here (AppRegistryNotReady).
# Import from submodules directly, e.g. ai_service.cover_letter.generate_cover_letter_from_raw_text

from .open_ai import (
    optimize_resume_for_job,
    optimize_my_resume_for_job,
    generate_professional_summary,
)

from .structured_resume import (
    format_resume,
    ResumeData,
    PersonalInfo,
    Experience,
    Education,
    Skills,
    Additional,
)


def __getattr__(name: str):
    """Lazy exports for modules that import Django models at load time."""
    if name == "generate_cover_letter_from_raw_text":
        from .cover_letter import generate_cover_letter_from_raw_text

        return generate_cover_letter_from_raw_text
    if name == "run_professional_summary_generation":
        from .professional_summary import run_professional_summary_generation

        return run_professional_summary_generation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "generate_cover_letter_from_raw_text",
    "optimize_resume_for_job",
    "optimize_my_resume_for_job",
    "generate_professional_summary",
    "run_professional_summary_generation",
    "format_resume",
    "ResumeData",
    "PersonalInfo",
    "Experience",
    "Education",
    "Skills",
    "Additional",
]
