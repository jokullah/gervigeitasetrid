# Generated by Django 5.2.1 on 2025-06-05 09:41

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertise', '0009_alter_projectpage_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='projectad',
            name='funding_amount',
            field=models.PositiveIntegerField(blank=True, help_text='Heildarfjárhæð verkefnisins í íslenskum krónum', null=True, verbose_name='Fjárhæð (ISK)'),
        ),
        migrations.AddField(
            model_name='projectad',
            name='is_funded',
            field=models.BooleanField(default=False, help_text='Krossa við ef verkefnið er fjármagnað', verbose_name='Fjármagnað verkefni'),
        ),
        migrations.AddField(
            model_name='projectad',
            name='requested_advisors',
            field=models.ManyToManyField(blank=True, help_text='Veljið starfsmenn sem þið viljið helst fá sem leiðbeinendur', limit_choices_to={'groups__name': 'Starfsmenn'}, related_name='requested_projects', to=settings.AUTH_USER_MODEL, verbose_name='Óskir um leiðbeinendur'),
        ),
        migrations.AddField(
            model_name='projectpage',
            name='funding_amount',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Fjárhæð (ISK)'),
        ),
        migrations.AddField(
            model_name='projectpage',
            name='is_funded',
            field=models.BooleanField(default=False, verbose_name='Fjármagnað verkefni'),
        ),
        migrations.AddField(
            model_name='projectpage',
            name='requested_advisors',
            field=models.ManyToManyField(blank=True, help_text='Starfsmenn sem fyrirtækið óskaði eftir sem leiðbeinendum', limit_choices_to={'groups__name': 'Starfsmenn'}, related_name='requested_project_pages', to=settings.AUTH_USER_MODEL, verbose_name='Óskir um leiðbeinendur'),
        ),
    ]
