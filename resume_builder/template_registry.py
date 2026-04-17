"""
Single source of truth for resume/CV HTML templates.

To add a template:
1. Add a row to RESUME_TEMPLATES (id must match filename: resume_templates/<id>.html).
2. Implement that template with a root element class ``<id>-template`` (e.g. executive-template).
3. Optional: set thumbnail_static to a path under static/ for gallery cards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Ordered list used everywhere: picker UI, APIs, AI enums, print CSS.
RESUME_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "professional",
        "name": "Professional",
        "description": "Clean and traditional design suitable for corporate environments",
        "short_label": "Classic, clean layout",
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

DEFAULT_TEMPLATE_ID: str = RESUME_TEMPLATES[0]["id"]

VALID_TEMPLATE_IDS: tuple[str, ...] = tuple(t["id"] for t in RESUME_TEMPLATES)

TEMPLATE_ID_ENUM: List[str] = list(VALID_TEMPLATE_IDS)


def is_valid_template_id(template_id: Optional[str]) -> bool:
    return bool(template_id) and template_id in VALID_TEMPLATE_IDS


def normalize_template_id(template_id: Optional[str]) -> str:
    if is_valid_template_id(template_id):
        return str(template_id)
    return DEFAULT_TEMPLATE_ID


def get_print_css_template_selectors() -> str:
    """Comma-separated class selectors for @media print (root class per template)."""
    return ", ".join(f".{t['id']}-template" for t in RESUME_TEMPLATES)


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
    return [{"id": t["id"], "name": t["name"]} for t in RESUME_TEMPLATES]


def templates_for_api() -> List[Dict[str, Any]]:
    """Full metadata for /resume/templates/ JSON API."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "features": list(t.get("features", [])),
        }
        for t in RESUME_TEMPLATES
    ]


def templates_for_gallery() -> List[Dict[str, Any]]:
    """Context for gallery + form cards (includes static thumbnail paths)."""
    return list(RESUME_TEMPLATES)
