import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0005_job_fit_gate_and_evaluation_user"),
        ("dashboard", "0005_job_application_detail_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="fit_evaluation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="job_applications",
                to="ai_service.resumejobevaluation",
            ),
        ),
    ]
