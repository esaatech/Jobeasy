# Generated manually: add DeepSeek to AIModel.provider choices.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_service", "0007_why_should_i_apply_answer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aimodel",
            name="provider",
            field=models.CharField(
                choices=[
                    ("gemini", "Google Gemini"),
                    ("openai", "OpenAI"),
                    ("deepseek", "DeepSeek"),
                ],
                default="gemini",
                max_length=32,
            ),
        ),
    ]
