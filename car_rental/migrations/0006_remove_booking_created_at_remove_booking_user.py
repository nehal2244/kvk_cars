# Generated by Django 5.2 on 2025-05-26 09:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('car_rental', '0005_booking'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='user',
        ),
    ]
