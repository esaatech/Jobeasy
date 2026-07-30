# Generated manually for Phase 1 job scraper

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_service', '0005_jobapplicationrequest_work_arrangements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='application_url',
            field=models.URLField(max_length=500),
        ),
        migrations.AddConstraint(
            model_name='job',
            constraint=models.UniqueConstraint(
                fields=('source', 'external_id'),
                condition=models.Q(external_id__gt=''),
                name='unique_job_source_external_id',
            ),
        ),
    ]
