from django.db import migrations


def forwards(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    new_row = {
        "template_id": "executive_portrait",
        "name": "Executive Portrait",
        "description": (
            "For directors and senior leaders who want measurable impact upfront. Same bold Executive "
            "layout with a portrait in the header—use when your leadership brand needs a face alongside outcomes."
        ),
        "role_label": "Executive / leadership",
        "short_label": "Bold header + portrait",
        "features": [
            "Executive header + photo",
            "Outcome-oriented",
            "Condensed timeline",
            "Leadership-ready",
        ],
        "thumbnail_static": "img/resume_templates/executive_portrait.svg",
        "selection_gradient": "from-slate-700 to-slate-900",
        "selection_title_class": "text-slate-100",
        "featured": False,
        "featured_rank": 5,
        "is_active": True,
    }
    ResumeTemplate.objects.update_or_create(template_id=new_row["template_id"], defaults=new_row)

    rank_updates = [
        ("portfolio", 6),
        ("ats_plain", 7),
        ("creative_studio", 8),
        ("studio_folio", 9),
        ("creative_atelier", 10),
    ]
    for template_id, rank in rank_updates:
        ResumeTemplate.objects.filter(template_id=template_id).update(featured_rank=rank)


def backwards(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(template_id="executive_portrait").delete()

    revert_ranks = [
        ("portfolio", 5),
        ("ats_plain", 6),
        ("creative_studio", 7),
        ("studio_folio", 8),
        ("creative_atelier", 9),
    ]
    for template_id, rank in revert_ranks:
        ResumeTemplate.objects.filter(template_id=template_id).update(featured_rank=rank)


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0009_seed_studio_folio_creative_atelier"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
