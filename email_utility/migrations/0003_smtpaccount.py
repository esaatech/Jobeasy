from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("email_utility", "0002_emailhistory_gmailauth_delete_emaillog"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SMTPAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("gmail", "Gmail"), ("outlook", "Outlook"), ("yahoo", "Yahoo Mail")], max_length=20)),
                ("email_address", models.EmailField(max_length=254)),
                ("app_password", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="smtp_accounts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "SMTP Account",
                "verbose_name_plural": "SMTP Accounts",
                "ordering": ["-is_default", "-updated_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="smtpaccount",
            constraint=models.UniqueConstraint(
                fields=("user", "provider", "email_address"),
                name="unique_user_provider_email_account",
            ),
        ),
    ]
