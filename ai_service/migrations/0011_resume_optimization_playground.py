# Generated manually: Resume optimization admin playground.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0010_cover_letter_playground"),
        ("resume_builder", "0011_gallery_section_student_templates"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResumeOptimizationPlayground",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Short label (e.g. “Acme backend role optimization test”).",
                        max_length=200,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="What you are testing—prompt version, resume variant, provider comparison, etc.",
                    ),
                ),
                ("job_description", models.TextField()),
                (
                    "resume_text",
                    models.TextField(
                        help_text="SOURCE_RESUME JSON: professional_summary, experience[], technical_skills, soft_skills, languages, projects[].",
                    ),
                ),
                ("model_used", models.CharField(blank=True, max_length=128)),
                ("temperature_used", models.FloatField(blank=True, null=True)),
                ("succeeded", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
                ("title", models.CharField(blank=True, max_length=512)),
                ("email_subject", models.CharField(blank=True, max_length=512)),
                ("optimized_summary", models.TextField(blank=True)),
                ("ats_score", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "result_json",
                    models.TextField(
                        blank=True,
                        help_text="Full merged optimization JSON from the last successful run.",
                    ),
                ),
                (
                    "instruction_slug",
                    models.SlugField(
                        blank=True,
                        help_text="Snapshot of prompt_configuration.slug used for versioning.",
                        max_length=80,
                    ),
                ),
                ("raw_response_text", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "ai_model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resume_optimization_playgrounds",
                        to="ai_service.aimodel",
                    ),
                ),
                (
                    "prompt_config",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resume_optimization_playgrounds",
                        to="ai_service.aipromptconfiguration",
                    ),
                ),
                (
                    "resume",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resume_optimization_playgrounds",
                        to="resume_builder.resume",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resume_optimization_playgrounds",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Resume optimization playground",
                "verbose_name_plural": "Resume optimization playground",
                "ordering": ["-created_at"],
            },
        ),
    ]
