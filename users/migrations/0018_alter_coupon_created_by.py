# Generated by Django 5.1.4 on 2025-04-24 05:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_coupon_is_new_customer'),
        ('vendors', '0029_subcategoryrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupons_created', to='vendors.vendor'),
        ),
    ]
