# Generated by Django 4.2.7 on 2024-12-29 17:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('product_account_transaction', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recharge',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
