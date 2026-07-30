from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0001_ultimate_automation_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='title_family_ai_generations',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Successful AI suggest-from-resume calls (free users capped)',
            ),
        ),
        migrations.AlterField(
            model_name='ultimateautomationprofile',
            name='auto_apply_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Requires Ultimate + confirmed title family',
            ),
        ),
    ]
