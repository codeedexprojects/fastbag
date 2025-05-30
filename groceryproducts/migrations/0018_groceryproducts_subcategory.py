# Generated by Django 5.1.4 on 2025-04-22 11:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groceryproducts', '0017_remove_groceryproducts_sub_category'),
        ('vendors', '0028_subcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='groceryproducts',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grocery', to='vendors.subcategory'),
        ),
    ]
