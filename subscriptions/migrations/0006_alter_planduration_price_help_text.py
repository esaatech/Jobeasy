from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0005_usersubscription_current_period_end_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planduration',
            name='price',
            field=models.DecimalField(
                decimal_places=2,
                help_text='Price in major units of STRIPE_BILLING_CURRENCY (default MXN), matching Stripe Price unit_amount.',
                max_digits=10,
            ),
        ),
    ]
