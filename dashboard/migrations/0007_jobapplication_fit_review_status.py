from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0006_jobapplication_fit_evaluation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("processing", "Processing"),
                    ("fit_review", "Fit Review"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="processing",
                max_length=20,
            ),
        ),
    ]
