# Generated by Django 5.1.3 on 2024-12-21 08:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodproduct', '0010_dishreport'),
        ('vendors', '0015_remove_vendor_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorBannerFoodProducts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('banner_image', models.ImageField(help_text='Upload the banner image', upload_to='banners/')),
                ('description', models.TextField(blank=True, help_text='Short description of the offer', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Only active banners will be displayed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='highlighted_in_banners', to='foodproduct.dish')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='food_banners', to='vendors.vendor')),
            ],
        ),
    ]
