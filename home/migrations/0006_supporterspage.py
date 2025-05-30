# Generated by Django 5.2.1 on 2025-05-28 10:19

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_aboutpage'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportersPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('intro', wagtail.fields.RichTextField(blank=True)),
                ('supporters', wagtail.fields.StreamField([('supporter', 3)], blank=True, block_lookup={0: ('wagtail.blocks.CharBlock', (), {'required': True}), 1: ('wagtail.images.blocks.ImageChooserBlock', (), {'required': False}), 2: ('wagtail.blocks.URLBlock', (), {'required': False}), 3: ('wagtail.blocks.StructBlock', [[('name', 0), ('logo', 1), ('website', 2)]], {})})),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
