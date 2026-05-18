from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0003_aimodel_and_generation_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="resumejobevaluation",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="Short label for this run (e.g. “Trend Micro Pro” or “Test resume v2”).",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="resumejobevaluation",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="What you are testing—resume variant, model comparison, job source, etc.",
            ),
        ),
        migrations.AddField(
            model_name="resumejobevaluation",
            name="conclusion",
            field=models.TextField(
                blank=True,
                help_text="Summary verdict; auto-filled from proceed_reasoning after a successful evaluation.",
            ),
        ),
    ]
