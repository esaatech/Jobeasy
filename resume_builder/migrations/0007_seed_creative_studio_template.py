from django.db import migrations


def seed_creative_studio(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    row = {
        "template_id": "creative_studio",
        "name": "Creative Studio",
        "description": (
            "Two-column creative layout with an organic photo mask, sidebar contact and skill bars, "
            "plus a structured references section—ideal when you want a portfolio-style CV."
        ),
        "role_label": "Creative / studio",
        "short_label": "Photo + refs + bars",
        "features": [
            "Clip-path portrait",
            "Rated skill bars",
            "References block",
            "Rich sidebar",
        ],
        "thumbnail_static": "img/resume_templates/creative_studio.svg",
        "selection_gradient": "from-amber-100 via-rose-50 to-violet-100",
        "selection_title_class": "text-violet-900",
        "featured": False,
        "featured_rank": 7,
        "is_active": True,
    }
    ResumeTemplate.objects.update_or_create(template_id=row["template_id"], defaults=row)


def unseed_creative_studio(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(template_id="creative_studio").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0006_seed_extra_resume_templates"),
    ]

    operations = [
        migrations.RunPython(seed_creative_studio, unseed_creative_studio),
    ]
