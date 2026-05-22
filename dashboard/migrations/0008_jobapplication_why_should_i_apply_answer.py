import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0007_why_should_i_apply_answer"),
        ("dashboard", "0007_jobapplication_fit_review_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="why_should_i_apply_answer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="job_applications",
                to="ai_service.whyshouldiapplyanswer",
            ),
        ),
    ]
