# Generated manually: Cover letter admin playground.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0009_professional_summary_playground"),
        ("resume_builder", "0011_gallery_section_student_templates"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CoverLetterPlayground",
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
                        help_text="Short label for this run (e.g. “Acme SWE cover letter test”).",
                        max_length=200,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="What you are testing—prompt variant, resume source, model comparison, etc.",
                    ),
                ),
                ("job_description", models.TextField()),
                ("resume_text", models.TextField()),
                (
                    "model_used",
                    models.CharField(
                        blank=True,
                        help_text="Model id snapshot from the last run.",
                        max_length=128,
                    ),
                ),
                (
                    "temperature_used",
                    models.FloatField(
                        blank=True,
                        help_text="Temperature used for this run.",
                        null=True,
                    ),
                ),
                ("succeeded", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
                ("title", models.CharField(blank=True, max_length=512)),
                ("email_subject", models.CharField(blank=True, max_length=512)),
                (
                    "cover_letter_text",
                    models.TextField(
                        blank=True,
                        help_text="Generated cover letter body.",
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
                        help_text="Model catalog row used for this run.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cover_letter_playgrounds",
                        to="ai_service.aimodel",
                    ),
                ),
                (
                    "prompt_config",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cover_letter_playgrounds",
                        to="ai_service.aipromptconfiguration",
                    ),
                ),
                (
                    "resume",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cover_letter_playgrounds",
                        to="resume_builder.resume",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cover_letter_playgrounds",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Cover letter playground",
                "verbose_name_plural": "Cover letter playground",
                "ordering": ["-created_at"],
            },
        ),
    ]
