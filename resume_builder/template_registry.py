"""
Single source of truth for resume/CV HTML templates.

To add a template:
1. Add or edit a ResumeTemplate in Django admin (template_id must match filename: resume_templates/<id>.html).
2. Implement that template with a root element class ``<id>-template`` (e.g. executive-template).
3. Optional: set thumbnail_static to a path under static/ for gallery cards.
4. Marketing /landing_page/resumes/: set ``featured`` True and ``featured_rank`` (1–4 typical);
   only featured templates appear there, capped at FEATURED_LANDING_MAX.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError

# Max featured templates shown on marketing landing pages (e.g. /landing_page/resumes/).
FEATURED_LANDING_MAX: int = 4


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
        "thumbnail_static": "img/resume_templates/professional.png",
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
        "thumbnail_static": "img/resume_templates/modern.png",
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
        "thumbnail_static": "img/resume_templates/creative.png",
        "selection_gradient": "from-purple-200 to-indigo-100",
        "selection_title_class": "text-purple-700",
    },
]

DEFAULT_TEMPLATE_ID: str = DEFAULT_RESUME_TEMPLATES[0]["id"]


def _normalize_template_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": record["id"],
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


def featured_templates_for_landing(max_count: int = FEATURED_LANDING_MAX) -> List[Dict[str, Any]]:
    """
    Templates marked featured=True, ordered by featured_rank (then list order).
    Used on marketing pages; max_count defaults to FEATURED_LANDING_MAX (4).
    """
    indexed = [(i, t) for i, t in enumerate(get_resume_templates()) if t.get("featured")]
    indexed.sort(key=lambda it: (it[1].get("featured_rank", 999), it[0]))
    return [t for _, t in indexed][:max_count]
