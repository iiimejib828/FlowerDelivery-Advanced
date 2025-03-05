# Generated by Django 5.1.6 on 2025-03-03 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WorkingHours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('mon', 'Понедельник'), ('tue', 'Вторник'), ('wed', 'Среда'), ('thu', 'Четверг'), ('fri', 'Пятница'), ('sat', 'Суббота'), ('sun', 'Воскресенье')], max_length=3, unique=True, verbose_name='День недели')),
                ('opening_time', models.TimeField(verbose_name='Время открытия')),
                ('closing_time', models.TimeField(verbose_name='Время закрытия')),
                ('is_working', models.BooleanField(default=True, verbose_name='Рабочий день')),
            ],
            options={
                'verbose_name': 'Рабочее время',
                'verbose_name_plural': 'Рабочее время',
            },
        ),
    ]
