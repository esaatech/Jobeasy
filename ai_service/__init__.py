# AI Service Package
from .open_ai import (
    generate_cover_letter_from_raw_text,
    optimize_resume_for_job,
    optimize_my_resume_for_job,
    generate_professional_summary
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
    # Legacy functions
    'generate_cover_letter_from_raw_text',
    'optimize_resume_for_job', 
    'optimize_my_resume_for_job',
    'generate_professional_summary',
    
    # New structured functions
    'format_resume',
    'ResumeData',
    'PersonalInfo',
    'Experience', 
    'Education',
    'Skills',
    'Additional'
]
