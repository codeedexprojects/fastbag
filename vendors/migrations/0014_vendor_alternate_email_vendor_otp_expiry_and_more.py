# Generated by Django 5.1.3 on 2024-12-12 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0013_alter_vendor_license'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='alternate_email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='otp_expiry',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='license',
            field=models.ImageField(upload_to='license'),
        ),
    ]
