# AI Service Package
from .cover_letter import generate_cover_letter_from_raw_text
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
    Additional
)

__all__ = [
    # Cover letter functions
    'generate_cover_letter_from_raw_text',
    
    # Resume optimization functions
    'optimize_resume_for_job', 
    'optimize_my_resume_for_job',
    'generate_professional_summary',
    'run_professional_summary_generation',
    
    # New structured functions
    'format_resume',
    'ResumeData',
    'PersonalInfo',
    'Experience', 
    'Education',
    'Skills',
    'Additional'
]
