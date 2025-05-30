# Generated by Django 3.2.10 on 2024-10-22 05:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GroceryCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('image', models.ImageField(blank=True, null=True, upload_to='category_images/')),
                ('Enable_category', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='GrocerySubCategories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='sample', max_length=100)),
                ('Sub_category_image', models.ImageField(blank=True, null=True, upload_to='category_images/')),
                ('Enable_subcategory', models.BooleanField(default=True)),
                ('Category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groceryproducts.grocerycategory')),
            ],
        ),
        migrations.CreateModel(
            name='GroceryProducts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('offer_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('discount', models.DecimalField(blank=True, decimal_places=2, help_text='Discount percentage', max_digits=5, null=True)),
                ('description', models.TextField(default='product')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('weight_measurement', models.CharField(max_length=100)),
                ('Available', models.BooleanField(default=True)),
                ('is_offer_product', models.BooleanField(default=False)),
                ('is_popular_product', models.BooleanField(default=False)),
                ('weights', models.JSONField(help_text='Store different weights with their respective prices, quantities, and stock status as a dictionary')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groceryproducts.grocerycategory')),
                ('sub_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='groceryproducts.grocerysubcategories')),
            ],
        ),
        migrations.CreateModel(
            name='GroceryProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/images/')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='groceryproducts.groceryproducts')),
            ],
        ),
    ]
