# Generated by Django 5.1.3 on 2025-01-04 05:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groceryproducts', '0009_grocerycouponusagecoupon_grocerycouponusage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GroceryCouponUsageCoupon',
            new_name='GroceryCoupon',
        ),
    ]
