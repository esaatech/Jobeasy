from django.db import migrations


def deactivate_yahoo_smtp_accounts(apps, schema_editor):
    # Retained as a no-op: Yahoo SMTP app-password sending is supported.
    return


def reactivate_yahoo_smtp_accounts(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("email_utility", "0004_yahooauth"),
    ]

    operations = [
        migrations.RunPython(
            deactivate_yahoo_smtp_accounts,
            reverse_code=reactivate_yahoo_smtp_accounts,
        ),
    ]
