# Generated by Django 5.1.6 on 2025-02-19 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Адрес доставки'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True, verbose_name='Номер телефона'),
        ),
    ]
