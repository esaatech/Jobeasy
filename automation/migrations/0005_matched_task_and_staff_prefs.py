# Generated manually for MatchedTask rename + packet fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def forwards_status(apps, schema_editor):
    MatchedTask = apps.get_model('automation', 'MatchedTask')
    MatchedTask.objects.filter(status='queued').update(status='matched')


def backwards_status(apps, schema_editor):
    MatchedTask = apps.get_model('automation', 'MatchedTask')
    MatchedTask.objects.filter(status='matched').update(status='queued')
    MatchedTask.objects.filter(status__in=['fit_paused', 'ready']).update(status='queued')


class Migration(migrations.Migration):

    dependencies = [
        ('ai_service', '0012_title_family_playground'),
        ('automation', '0004_apply_task'),
        ('coverletter', '0003_coverletter_job_description'),
        ('job_service', '0007_job_work_arrangement'),
        ('resume_builder', '0011_gallery_section_student_templates'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ApplyTask',
            new_name='MatchedTask',
        ),
        migrations.AlterModelOptions(
            name='matchedtask',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Matched task',
                'verbose_name_plural': 'Matched tasks',
            },
        ),
        migrations.RemoveConstraint(
            model_name='matchedtask',
            name='unique_apply_task_user_job',
        ),
        migrations.AlterField(
            model_name='matchedtask',
            name='job',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='matched_tasks',
                to='job_service.job',
            ),
        ),
        migrations.AlterField(
            model_name='matchedtask',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='matched_tasks',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='matchedtask',
            name='status',
            field=models.CharField(
                choices=[
                    ('matched', 'Matched'),
                    ('fit_paused', 'Fit paused'),
                    ('ready', 'Ready to apply'),
                    ('applied', 'Applied'),
                    ('skipped', 'Skipped'),
                    ('queued', 'Queued'),  # temporary during data migration
                ],
                db_index=True,
                default='matched',
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards_status, backwards_status),
        migrations.AlterField(
            model_name='matchedtask',
            name='status',
            field=models.CharField(
                choices=[
                    ('matched', 'Matched'),
                    ('fit_paused', 'Fit paused'),
                    ('ready', 'Ready to apply'),
                    ('applied', 'Applied'),
                    ('skipped', 'Skipped'),
                ],
                db_index=True,
                default='matched',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='matchedtask',
            name='skip_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('captcha', 'CAPTCHA'),
                    ('login_required', 'Login required'),
                    ('job_closed', 'Job closed'),
                    ('geo_block', 'Geo blocked'),
                    ('email_only', 'Email-only apply'),
                    ('weak_fit', 'Weak / paused fit'),
                    ('other', 'Other'),
                ],
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='fit_evaluation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matched_tasks',
                to='ai_service.resumejobevaluation',
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='fit_summary',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Dashboard-shaped fit summary (score, recommendation, strengths, gaps).',
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='fit_tier',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='source_resume',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matched_tasks_as_source',
                to='resume_builder.resume',
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='optimized_resume',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matched_tasks_as_optimized',
                to='resume_builder.resume',
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='cover_letter',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matched_tasks',
                to='coverletter.coverletter',
            ),
        ),
        migrations.AddField(
            model_name='matchedtask',
            name='why_should_i_apply_answer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matched_tasks',
                to='ai_service.whyshouldiapplyanswer',
            ),
        ),
        migrations.AddConstraint(
            model_name='matchedtask',
            constraint=models.UniqueConstraint(
                fields=('user', 'job'),
                name='unique_matched_task_user_job',
            ),
        ),
        migrations.CreateModel(
            name='StaffMatchRunPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('optimize_resume', models.BooleanField(default=False)),
                ('generate_cover_letter', models.BooleanField(default=False)),
                ('generate_why_should_hire', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='ultimate_match_run_preferences',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Staff match-run preferences',
                'verbose_name_plural': 'Staff match-run preferences',
            },
        ),
    ]
