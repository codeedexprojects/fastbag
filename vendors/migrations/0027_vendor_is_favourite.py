# Generated by Django 5.1.4 on 2025-03-04 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0026_vendor_latitude_vendor_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='is_favourite',
            field=models.BooleanField(default=False),
        ),
    ]
