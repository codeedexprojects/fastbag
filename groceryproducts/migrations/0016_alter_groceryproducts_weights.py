# Generated by Django 5.1.4 on 2025-03-13 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groceryproducts', '0015_rename_available_groceryproducts_is_available'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groceryproducts',
            name='weights',
            field=models.JSONField(default=list, help_text='Store different weights with their respective prices, quantities, and stock status as a dictionary'),
        ),
    ]
