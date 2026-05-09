# Generated manually: align gallery thumbnails with Row 2 style (SVG document card).

from django.db import migrations


THUMB_MAP = {
    "professional": "img/resume_templates/professional.svg",
    "modern": "img/resume_templates/modern.svg",
    "creative": "img/resume_templates/creative.svg",
}


def forwards(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    for tid, path in THUMB_MAP.items():
        ResumeTemplate.objects.filter(template_id=tid).update(thumbnail_static=path)


def backwards(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    revert = {
        "professional": "img/resume_templates/professional.png",
        "modern": "img/resume_templates/modern.png",
        "creative": "img/resume_templates/creative.png",
    }
    for tid, path in revert.items():
        ResumeTemplate.objects.filter(template_id=tid).update(thumbnail_static=path)


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0007_seed_creative_studio_template"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
