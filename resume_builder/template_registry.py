"""
Single source of truth for resume/CV HTML templates.

To add a template:
1. Add or edit a ResumeTemplate in Django admin (template_id must match filename: resume_templates/<id>.html).
2. Implement that template with a root element class ``<id>-template`` (e.g. executive-template).
3. Optional: set thumbnail_static to a path under static/ for gallery cards.
4. Marketing /landing_page/resumes/: set ``featured`` True and ``featured_rank`` (1–4 typical);
   only featured templates appear there, capped at FEATURED_LANDING_MAX.
5. Gallery grouping: set ``gallery_section`` (``general`` vs ``students``) on templates and in Django admin;
   the public / wizard UI renders subsection headings for general templates, then a "Students & recent grads" block.

Wizard-only sections (optional photo, extended contact rows, references repeater, rated-skills panel) are shown
only for template IDs listed in ``_TEMPLATE_CAPABILITY_OVERRIDES`` (photo-forward and Executive Portrait layouts).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError

# Max featured templates shown on marketing landing pages (e.g. /landing_page/resumes/).
FEATURED_LANDING_MAX: int = 4

# Gallery / wizard grouping (matches ResumeTemplate.GallerySection in models).
GALLERY_SECTION_GENERAL: str = "general"
GALLERY_SECTION_STUDENTS: str = "students"
STUDENT_GALLERY_SECTION_HEADING: str = "Students & recent grads"

# General gallery: ordered subsections (each row is typically 3 cards on lg grids).
GENERAL_GALLERY_SUBSECTIONS: List[Tuple[str, Tuple[str, ...]]] = [
    ("Classic & contemporary", ("professional", "modern", "creative")),
    ("Leadership & portfolio", ("executive", "executive_portrait", "portfolio")),
    ("Creative studios", ("ats_plain", "creative_studio", "studio_folio", "creative_atelier")),
]
GENERAL_GALLERY_LEFTOVER_HEADING: str = "More layouts"

# Wizard/UI: optional fields rendered only when the selected template supports them (data retained if user switches templates).
_CAPABILITY_KEYS: tuple[str, ...] = (
    "supports_extended_contact",
    "supports_profile_photo",
    "supports_references",
    "supports_rated_skills",
)

_BLANK_CAPABILITY_FLAGS: Dict[str, bool] = {k: False for k in _CAPABILITY_KEYS}

# Only templates listed here expose extra wizard sections; defaults are False for everyone else (including unknown DB slug).
_TEMPLATE_CAPABILITY_OVERRIDES: Dict[str, Dict[str, bool]] = {
    "creative_studio": {k: True for k in _CAPABILITY_KEYS},
    "studio_folio": {k: True for k in _CAPABILITY_KEYS},
    "creative_atelier": {k: True for k in _CAPABILITY_KEYS},
    "executive_portrait": {
        "supports_extended_contact": True,
        "supports_profile_photo": True,
        "supports_references": False,
        "supports_rated_skills": False,
    },
}


def template_ui_capabilities(template_id: Optional[str]) -> Dict[str, bool]:
    """Return booleans shaping the resume-builder wizard for this layout.

    Uses a plain slug lookup (not normalize_template_id) to avoid circular imports:
    _normalize_template_record → template_ui_capabilities during get_resume_templates bootstrap.
    """
    tid = str(template_id or "").strip()
    out = dict(_BLANK_CAPABILITY_FLAGS)
    out.update(_TEMPLATE_CAPABILITY_OVERRIDES.get(tid, {}))
    return out


# Fallback list used when DB is not available yet (migrations/bootstrap).
DEFAULT_RESUME_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "professional",
        "name": "Professional",
        "description": "Clean and traditional design suitable for corporate environments",
        "short_label": "Classic, clean layout",
        "featured": True,
        "featured_rank": 1,
        "features": [
            "ATS-friendly",
            "Clean layout",
            "Professional fonts",
            "Standard sections",
        ],
        "thumbnail_static": "img/resume_templates/professional.svg",
        "selection_gradient": "from-gray-200 to-gray-100",
        "selection_title_class": "text-gray-700",
    },
    {
        "id": "modern",
        "name": "Modern",
        "description": "Contemporary design with modern styling and layout",
        "short_label": "Contemporary, bold headings",
        "featured": True,
        "featured_rank": 2,
        "features": [
            "Modern typography",
            "Color accents",
            "Creative layout",
            "Visual hierarchy",
        ],
        "thumbnail_static": "img/resume_templates/modern.svg",
        "selection_gradient": "from-blue-200 to-blue-100",
        "selection_title_class": "text-blue-700",
    },
    {
        "id": "creative",
        "name": "Creative",
        "description": "Unique and eye-catching design for creative industries",
        "short_label": "Colorful, eye-catching",
        "featured": True,
        "featured_rank": 3,
        "features": [
            "Unique layout",
            "Creative elements",
            "Colorful design",
            "Stand out",
        ],
        "thumbnail_static": "img/resume_templates/creative.svg",
        "selection_gradient": "from-purple-200 to-indigo-100",
        "selection_title_class": "text-purple-700",
    },
    {
        "id": "executive",
        "name": "Executive",
        "description": (
            "For directors and senior leaders who want measurable impact upfront. Bold header, condensed "
            "roles, and a layout that favors outcomes over long task lists."
        ),
        "role_label": "Executive / leadership",
        "short_label": "Impact-focused header",
        "featured": False,
        "featured_rank": 4,
        "features": [
            "Executive header",
            "Outcome-oriented",
            "Condensed timeline",
            "Leadership-ready",
        ],
        "thumbnail_static": "img/resume_templates/executive.svg",
        "selection_gradient": "from-slate-700 to-slate-900",
        "selection_title_class": "text-slate-100",
    },
    {
        "id": "executive_portrait",
        "name": "Executive Portrait",
        "description": (
            "For directors and senior leaders who want measurable impact upfront. Same bold Executive "
            "layout with a portrait in the header—use when your leadership brand needs a face alongside outcomes."
        ),
        "role_label": "Executive / leadership",
        "short_label": "Bold header + portrait",
        "featured": False,
        "featured_rank": 5,
        "features": [
            "Executive header + photo",
            "Outcome-oriented",
            "Condensed timeline",
            "Leadership-ready",
        ],
        "thumbnail_static": "img/resume_templates/executive_portrait.svg",
        "selection_gradient": "from-slate-700 to-slate-900",
        "selection_title_class": "text-slate-100",
    },
    {
        "id": "portfolio",
        "name": "Portfolio",
        "description": (
            "Freelancers, consultants, and builders: foreground your projects and engagements, "
            "then back them up with experience and education. Skills live in a clear sidebar."
        ),
        "role_label": "Project / portfolio",
        "short_label": "Projects first",
        "featured": False,
        "featured_rank": 6,
        "features": [
            "Projects spotlight",
            "Sidebar skills",
            "Engagement-ready",
            "Flexible story",
        ],
        "thumbnail_static": "img/resume_templates/portfolio.svg",
        "selection_gradient": "from-teal-100 to-teal-50",
        "selection_title_class": "text-teal-900",
    },
    {
        "id": "ats_plain",
        "name": "ATS Plain",
        "description": (
            "Simple single-column layout with standard headings and comma-separated skills. "
            "Optimizes readability for applicant tracking systems and quick recruiter scans."
        ),
        "role_label": "ATS plain",
        "short_label": "Parser-friendly",
        "featured": False,
        "featured_rank": 7,
        "features": [
            "Single column",
            "Standard headings",
            "Minimal styling",
            "High parse reliability",
        ],
        "thumbnail_static": "img/resume_templates/ats_plain.svg",
        "selection_gradient": "from-neutral-100 to-white",
        "selection_title_class": "text-neutral-900",
    },
    {
        "id": "creative_studio",
        "name": "Creative Studio",
        "description": (
            "Two-column creative layout with an organic photo mask, sidebar contact and skill bars, "
            "plus a structured references section—ideal when you want a portfolio-style CV."
        ),
        "role_label": "Creative / studio",
        "short_label": "Photo + refs + bars",
        "featured": False,
        "featured_rank": 8,
        "features": [
            "Clip-path portrait",
            "Rated skill bars",
            "References block",
            "Rich sidebar",
        ],
        "thumbnail_static": "img/resume_templates/creative_studio.svg",
        "selection_gradient": "from-amber-100 via-rose-50 to-violet-100",
        "selection_title_class": "text-violet-900",
    },
    {
        "id": "studio_folio",
        "name": "Studio Folio",
        "description": (
            "Portrait-centered header with a two-column experience grid, selected-work spotlight, "
            "and the same organic portrait mask as other creative templates—ideal for designers and makers."
        ),
        "role_label": "Portfolio / studio",
        "short_label": "Folio grid + portrait",
        "featured": False,
        "featured_rank": 9,
        "features": [
            "Work-forward layout",
            "Experience cards",
            "Unified portrait mask",
            "Rated + soft skills",
        ],
        "thumbnail_static": "img/resume_templates/studio_folio.svg",
        "selection_gradient": "from-stone-200 via-orange-50 to-stone-100",
        "selection_title_class": "text-stone-900",
    },
    {
        "id": "creative_atelier",
        "name": "Creative Atelier",
        "description": (
            "Editorial main column for your story plus a right-rail sidebar for the portrait, contact, "
            "rated skills, and references—with identical portrait treatment when switching from Creative Studio."
        ),
        "role_label": "Editorial / atelier",
        "short_label": "Narrative + side portrait",
        "featured": False,
        "featured_rank": 10,
        "features": [
            "Narrative-first column",
            "Right sidebar portrait",
            "Rated skill bars",
            "References block",
        ],
        "thumbnail_static": "img/resume_templates/creative_atelier.svg",
        "selection_gradient": "from-rose-100 via-white to-slate-200",
        "selection_title_class": "text-slate-900",
    },
    {
        "id": "new_grad_ats",
        "name": "Campus ATS",
        "description": (
            "Minimal single-column layout with education and projects up front—built for campus recruiting "
            "and applicant tracking systems when you are light on formal work history."
        ),
        "role_label": "Student / new grad · ATS",
        "short_label": "Education + keywords first",
        "featured": False,
        "featured_rank": 11,
        "gallery_section": GALLERY_SECTION_STUDENTS,
        "features": [
            "Single column",
            "Education-forward",
            "Projects block",
            "Parser-friendly skills",
        ],
        "thumbnail_static": "img/resume_templates/new_grad_ats.svg",
        "selection_gradient": "from-slate-100 to-white",
        "selection_title_class": "text-slate-800",
    },
    {
        "id": "new_grad_projects",
        "name": "Project Focus",
        "description": (
            "Highlights coursework and projects in the main column with a skills sidebar—ideal for CS, design, "
            "and builders who want proof before job titles."
        ),
        "role_label": "Student / new grad · Projects",
        "short_label": "Projects + skills rail",
        "featured": False,
        "featured_rank": 12,
        "gallery_section": GALLERY_SECTION_STUDENTS,
        "features": [
            "Projects first",
            "Print-safe two column",
            "Sidebar skills",
            "Internships supported",
        ],
        "thumbnail_static": "img/resume_templates/new_grad_projects.svg",
        "selection_gradient": "from-indigo-100 to-indigo-50",
        "selection_title_class": "text-indigo-900",
    },
    {
        "id": "new_grad_profile",
        "name": "Campus Profile",
        "description": (
            "Clear single-column flow: summary, education, then experience for internships, clubs, and "
            "volunteering—without looking like an executive layout."
        ),
        "role_label": "Student / new grad · Activities",
        "short_label": "Activities + education",
        "featured": False,
        "featured_rank": 13,
        "gallery_section": GALLERY_SECTION_STUDENTS,
        "features": [
            "Single column",
            "Scannable sections",
            "Leadership-friendly",
            "PDF-safe layout",
        ],
        "thumbnail_static": "img/resume_templates/new_grad_profile.svg",
        "selection_gradient": "from-sky-100 to-slate-50",
        "selection_title_class": "text-sky-900",
    },
]

DEFAULT_TEMPLATE_ID: str = DEFAULT_RESUME_TEMPLATES[0]["id"]


def _normalize_template_record(record: Dict[str, Any]) -> Dict[str, Any]:
    tid = record["id"]
    caps = template_ui_capabilities(tid)
    for key in _CAPABILITY_KEYS:
        if key in record:
            caps[key] = bool(record[key])
    return {
        "id": tid,
        "name": record.get("name", ""),
        "description": record.get("description", ""),
        "role_label": record.get("role_label") or record.get("name", ""),
        "short_label": record.get("short_label", ""),
        "featured": bool(record.get("featured", False)),
        "featured_rank": int(record.get("featured_rank", 999)),
        "features": list(record.get("features", [])),
        "thumbnail_static": record.get("thumbnail_static", ""),
        "selection_gradient": record.get("selection_gradient", ""),
        "selection_title_class": record.get("selection_title_class", ""),
        "is_active": bool(record.get("is_active", True)),
        "gallery_section": str(record.get("gallery_section", GALLERY_SECTION_GENERAL)),
        **caps,
    }


def _template_model():
    try:
        return apps.get_model("resume_builder", "ResumeTemplate")
    except (LookupError, AppRegistryNotReady):
        return None


def _iter_db_templates() -> Iterable[Dict[str, Any]]:
    model = _template_model()
    if model is None:
        return []

    try:
        templates = model.objects.filter(is_active=True).order_by("featured_rank", "name")
        return [
            _normalize_template_record(
                {
                    "id": item.template_id,
                    "name": item.name,
                    "description": item.description,
                    "role_label": item.role_label,
                    "short_label": item.short_label,
                    "featured": item.featured,
                    "featured_rank": item.featured_rank,
                    "features": item.features,
                    "thumbnail_static": item.thumbnail_static,
                    "selection_gradient": item.selection_gradient,
                    "selection_title_class": item.selection_title_class,
                    "is_active": item.is_active,
                    "gallery_section": getattr(
                        item, "gallery_section", GALLERY_SECTION_GENERAL
                    ),
                }
            )
            for item in templates
        ]
    except (OperationalError, ProgrammingError):
        return []


def _default_templates() -> List[Dict[str, Any]]:
    return [_normalize_template_record(item) for item in DEFAULT_RESUME_TEMPLATES]


def get_resume_templates() -> List[Dict[str, Any]]:
    db_templates = list(_iter_db_templates())
    if db_templates:
        return db_templates
    return _default_templates()


def get_valid_template_ids() -> tuple[str, ...]:
    ids = tuple(t["id"] for t in get_resume_templates())
    if ids:
        return ids
    return (DEFAULT_TEMPLATE_ID,)


def get_template_id_enum() -> List[str]:
    return list(get_valid_template_ids())


# Import-safe fallback constants (no DB access at module import).
VALID_TEMPLATE_IDS: tuple[str, ...] = tuple(t["id"] for t in DEFAULT_RESUME_TEMPLATES)
TEMPLATE_ID_ENUM: List[str] = list(VALID_TEMPLATE_IDS)


def is_valid_template_id(template_id: Optional[str]) -> bool:
    return bool(template_id) and template_id in get_valid_template_ids()


def normalize_template_id(template_id: Optional[str]) -> str:
    if is_valid_template_id(template_id):
        return str(template_id)
    return DEFAULT_TEMPLATE_ID


def get_print_css_template_selectors() -> str:
    """Comma-separated class selectors for @media print (root class per template)."""
    return ", ".join(f".{t['id']}-template" for t in get_resume_templates())


def get_resume_embedded_style_tag() -> str:
    """Full <style> block for resume HTML embeds (view/download) with Tailwind CDN."""
    sel = get_print_css_template_selectors()
    return f"""    <style>
        @media print {{
            body {{ margin: 0; padding: 20px; }}
            {sel} {{
                max-width: none; box-shadow: none;
            }}
        }}
    </style>"""


def templates_for_download_picker() -> List[Dict[str, str]]:
    """Minimal {id, name} for session-based download flow."""
    return [{"id": t["id"], "name": t["name"]} for t in get_resume_templates()]


def templates_for_api() -> List[Dict[str, Any]]:
    """Full metadata for /resume/templates/ JSON API."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "features": list(t.get("features", [])),
        }
        for t in get_resume_templates()
    ]


def templates_for_gallery() -> List[Dict[str, Any]]:
    """Context for gallery + form cards (includes static thumbnail paths)."""
    return list(get_resume_templates())


def get_resume_template_gallery_sections() -> List[Dict[str, Any]]:
    """Ordered sections for gallery UI: general subsections (3-row style groups), then students."""
    all_t = get_resume_templates()
    general = [
        t
        for t in all_t
        if t.get("gallery_section", GALLERY_SECTION_GENERAL) == GALLERY_SECTION_GENERAL
    ]
    students = [t for t in all_t if t.get("gallery_section") == GALLERY_SECTION_STUDENTS]
    sections: List[Dict[str, Any]] = []

    if general:
        general_by_id = {t["id"]: t for t in general}
        assigned: set[str] = set()
        for heading, ids in GENERAL_GALLERY_SUBSECTIONS:
            bucket = [general_by_id[i] for i in ids if i in general_by_id]
            assigned.update(t["id"] for t in bucket)
            if bucket:
                sections.append({"heading": heading, "templates": bucket})
        leftover = [t for t in general if t["id"] not in assigned]
        if leftover:
            sections.append(
                {"heading": GENERAL_GALLERY_LEFTOVER_HEADING, "templates": leftover}
            )

    if students:
        sections.append(
            {"heading": STUDENT_GALLERY_SECTION_HEADING, "templates": students}
        )

    if not sections:
        sections.append({"heading": None, "templates": all_t})
    return sections


def featured_templates_for_landing(max_count: int = FEATURED_LANDING_MAX) -> List[Dict[str, Any]]:
    """
    Templates marked featured=True, ordered by featured_rank (then list order).
    Used on marketing pages; max_count defaults to FEATURED_LANDING_MAX (4).
    """
    indexed = [(i, t) for i, t in enumerate(get_resume_templates()) if t.get("featured")]
    indexed.sort(key=lambda it: (it[1].get("featured_rank", 999), it[0]))
    return [t for _, t in indexed][:max_count]
