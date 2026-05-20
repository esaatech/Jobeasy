import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0004_resumejobevaluation_label_fields"),
        ("resume_builder", "0011_gallery_section_student_templates"),
        ("dashboard", "0005_job_application_detail_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JobFitGateSettings",
            fields=[
                (
                    "id",
                    models.PositiveSmallIntegerField(
                        default=1,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(
                        default=True,
                        help_text="When off, dashboard skips evaluation and uses the legacy generate flow.",
                    ),
                ),
                (
                    "green_min_score",
                    models.PositiveSmallIntegerField(
                        default=70,
                        help_text="Scores at or above this (with Good/Strong recommendation) auto-proceed.",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "yellow_min_score",
                    models.PositiveSmallIntegerField(
                        default=50,
                        help_text="Scores below green_min but at or above this require user confirmation.",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "prompt_config",
                    models.ForeignKey(
                        blank=True,
                        help_text="Evaluator prompt used for dashboard fit checks.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="job_fit_gate_settings",
                        to="ai_service.aipromptconfiguration",
                    ),
                ),
            ],
            options={
                "verbose_name": "Job fit gate settings",
                "verbose_name_plural": "Job fit gate settings",
            },
        ),
        migrations.AddField(
            model_name="resumejobevaluation",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resume_job_evaluations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="resumejobevaluation",
            name="resume",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="resume_job_evaluations",
                to="resume_builder.resume",
            ),
        ),
        migrations.AddField(
            model_name="resumejobevaluation",
            name="job_application",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="fit_evaluations",
                to="dashboard.jobapplication",
            ),
        ),
    ]
