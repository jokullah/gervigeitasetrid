# Generated by Django 5.2.1 on 2025-06-05 14:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertise', '0010_projectad_funding_amount_projectad_is_funded_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='projectpage',
            name='selected_students',
            field=models.ManyToManyField(blank=True, help_text='Nemendur sem hafa verið valdir fyrir þetta verkefni', limit_choices_to={'groups__name': 'Nemandi'}, related_name='assigned_projects', to=settings.AUTH_USER_MODEL, verbose_name='Valdir nemendur'),
        ),
        migrations.CreateModel(
            name='ProjectApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applied_at', models.DateTimeField(auto_now_add=True, verbose_name='Umsókn send')),
                ('status', models.CharField(choices=[('pending', 'Í bið'), ('accepted', 'Samþykkt'), ('rejected', 'Hafnað')], default='pending', max_length=20, verbose_name='Staða')),
                ('message', models.TextField(blank=True, help_text='Valfrjáls skilaboð frá umsækjanda', verbose_name='Skilaboð frá nemanda')),
                ('applicant', models.ForeignKey(limit_choices_to={'groups__name': 'Nemandi'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Umsækjandi')),
                ('project_page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='advertise.projectpage', verbose_name='Verkefni')),
            ],
            options={
                'verbose_name': 'Verkefnisumsókn',
                'verbose_name_plural': 'Verkefnisumsóknir',
                'ordering': ['-applied_at'],
                'unique_together': {('project_page', 'applicant')},
            },
        ),
    ]
