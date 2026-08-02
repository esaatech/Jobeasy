from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0002_title_family_ai_generations'),
    ]

    operations = [
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='distance_miles',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Preferred commute / search radius in miles',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='other_purpose',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='preferred_countries',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Selected countries/states, e.g. [{"name":"Canada","cca2":"CA","states":["Ontario"]}]',
            ),
        ),
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='search_purpose',
            field=models.CharField(
                blank=True,
                choices=[
                    ('career_growth', 'Career Growth & Advancement'),
                    ('better_compensation', 'Better Compensation & Benefits'),
                    ('work_life_balance', 'Better Work-Life Balance'),
                    ('relocation', 'Relocation to New City/Country'),
                    ('travel_opportunity', 'Travel & Work Abroad'),
                    ('industry_change', 'Change of Industry'),
                    ('company_culture', 'Better Company Culture'),
                    ('remote_work', 'Remote Work Opportunities'),
                    ('other', 'Other'),
                ],
                help_text='Why the user is looking for roles',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='ultimateautomationprofile',
            name='work_arrangements',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Preferred arrangements: remote, hybrid, onsite',
            ),
        ),
    ]
