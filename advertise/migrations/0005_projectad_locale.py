# Generated by Django 5.2.1 on 2025-06-04 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertise', '0004_projectad_project_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectad',
            name='locale',
            field=models.CharField(choices=[('is', 'Íslenska'), ('en', 'English')], default='is', help_text='Tungumál vefsíðunnar þegar auglýsingin var send inn', max_length=10, verbose_name='Tungumál'),
        ),
    ]
