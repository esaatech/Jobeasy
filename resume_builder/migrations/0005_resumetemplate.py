from django.db import migrations, models


def seed_resume_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")

    initial_templates = [
        {
            "template_id": "professional",
            "name": "Professional",
            "description": "Clean and traditional design suitable for corporate environments",
            "role_label": "Professional",
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
            "featured": True,
            "featured_rank": 1,
            "is_active": True,
        },
        {
            "template_id": "modern",
            "name": "Modern",
            "description": "Contemporary design with modern styling and layout",
            "role_label": "Tech",
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
            "featured": True,
            "featured_rank": 2,
            "is_active": True,
        },
        {
            "template_id": "creative",
            "name": "Creative",
            "description": "Unique and eye-catching design for creative industries",
            "role_label": "Recent Graduate",
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
            "featured": True,
            "featured_rank": 3,
            "is_active": True,
        },
    ]

    for row in initial_templates:
        ResumeTemplate.objects.update_or_create(template_id=row["template_id"], defaults=row)


def unseed_resume_templates(apps, schema_editor):
    ResumeTemplate = apps.get_model("resume_builder", "ResumeTemplate")
    ResumeTemplate.objects.filter(template_id__in=["professional", "modern", "creative"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("resume_builder", "0004_resume_relevant_experience"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResumeTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("template_id", models.SlugField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("role_label", models.CharField(blank=True, default="", max_length=100)),
                ("short_label", models.CharField(blank=True, default="", max_length=120)),
                ("features", models.JSONField(blank=True, default=list)),
                ("thumbnail_static", models.CharField(blank=True, default="", max_length=255)),
                ("selection_gradient", models.CharField(blank=True, default="", max_length=120)),
                ("selection_title_class", models.CharField(blank=True, default="", max_length=120)),
                ("featured", models.BooleanField(default=False)),
                ("featured_rank", models.PositiveIntegerField(default=999)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["featured_rank", "name"]},
        ),
        migrations.RunPython(seed_resume_templates, unseed_resume_templates),
    ]
