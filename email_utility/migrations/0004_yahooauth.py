import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("email_utility", "0003_smtpaccount"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="YahooAuth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("access_token", models.TextField()),
                ("refresh_token", models.TextField()),
                ("token_expiry", models.DateTimeField()),
                ("yahoo_address", models.EmailField(max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="yahoo_auth", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Yahoo Authentication",
                "verbose_name_plural": "Yahoo Authentications",
            },
        ),
    ]
