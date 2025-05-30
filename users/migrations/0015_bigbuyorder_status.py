# Generated by Django 5.1.4 on 2025-04-16 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_bigbuyorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='bigbuyorder',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('PREPARING', 'Preparing'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20),
        ),
    ]
