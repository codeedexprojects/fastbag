# Generated by Django 5.1.3 on 2024-12-19 09:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groceryproducts', '0005_groceryproducts_vendor'),
        ('users', '0006_remove_address_email_remove_address_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grocery_wishlist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grocery', to='users.customuser'),
        ),
        migrations.AlterField(
            model_name='groceryproductreview',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_reviews', to='users.customuser'),
        ),
    ]
