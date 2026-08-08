from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0005_matched_task_and_staff_prefs'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchedtask',
            name='fit_score',
            field=models.PositiveSmallIntegerField(
                blank=True,
                db_index=True,
                help_text='Denormalized overall fit score for list sorting.',
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name='matchedtask',
            index=models.Index(
                fields=['status', 'fit_score'],
                name='matchedtask_status_fit_idx',
            ),
        ),
    ]
