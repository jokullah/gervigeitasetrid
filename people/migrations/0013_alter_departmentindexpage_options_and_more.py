# Generated by Django 5.2.1 on 2025-06-12 10:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0012_merge_20250611_1315'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='departmentindexpage',
            options={'verbose_name': 'Hópasíða', 'verbose_name_plural': 'Hópasíður'},
        ),
        migrations.AlterModelOptions(
            name='peopleindexpage',
            options={'verbose_name': 'Fólksíða', 'verbose_name_plural': 'Fólksíður'},
        ),
        migrations.AlterModelOptions(
            name='personpage',
            options={'verbose_name': 'Starfsmannasíða', 'verbose_name_plural': 'Starfsmannasíður'},
        ),
    ]
