# Generated by Django 5.2.1 on 2025-06-04 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('car_rental', '0010_remove_car_price_400km_car_image_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='extra_hour_charge',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Charge per hour after 12 hours rental', max_digits=6),
        ),
    ]
