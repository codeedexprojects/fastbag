# Generated by Django 5.1.3 on 2024-12-12 08:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groceryproducts', '0003_groceryproductreview'),
        ('vendors', '0014_vendor_alternate_email_vendor_otp_expiry_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grocerycategory',
            name='Description',
            field=models.CharField(default='Category Description', max_length=1000),
        ),
        migrations.AddField(
            model_name='grocerycategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='grocerycategory',
            name='store',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='vendors.vendor'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='grocerysubcategories',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
