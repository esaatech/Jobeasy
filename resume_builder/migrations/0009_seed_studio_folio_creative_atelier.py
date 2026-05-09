from django.db import migrations


def seed_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    rows = [
        {
            "template_id": "studio_folio",
            "name": "Studio Folio",
            "description": (
                "Portrait-centered header with a two-column experience grid, selected-work spotlight, "
                "and the same organic portrait mask as other creative templates—ideal for designers and makers."
            ),
            "role_label": "Portfolio / studio",
            "short_label": "Folio grid + portrait",
            "features": [
                "Work-forward layout",
                "Experience cards",
                "Unified portrait mask",
                "Rated + soft skills",
            ],
            "thumbnail_static": "img/resume_templates/studio_folio.svg",
            "selection_gradient": "from-stone-200 via-orange-50 to-stone-100",
            "selection_title_class": "text-stone-900",
            "featured": False,
            "featured_rank": 8,
            "is_active": True,
        },
        {
            "template_id": "creative_atelier",
            "name": "Creative Atelier",
            "description": (
                "Editorial main column for your story plus a right-rail sidebar for the portrait, contact, "
                "rated skills, and references—with identical portrait treatment when switching from Creative Studio."
            ),
            "role_label": "Editorial / atelier",
            "short_label": "Narrative + side portrait",
            "features": [
                "Narrative-first column",
                "Right sidebar portrait",
                "Rated skill bars",
                "References block",
            ],
            "thumbnail_static": "img/resume_templates/creative_atelier.svg",
            "selection_gradient": "from-rose-100 via-white to-slate-200",
            "selection_title_class": "text-slate-900",
            "featured": False,
            "featured_rank": 9,
            "is_active": True,
        },
    ]
    for row in rows:
        ResumeTemplate.objects.update_or_create(template_id=row["template_id"], defaults=row)


def unseed_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(template_id__in=("studio_folio", "creative_atelier")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0008_row1_template_svg_thumbnails"),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
