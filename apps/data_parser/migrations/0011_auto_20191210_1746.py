# Generated by Django 3.0 on 2019-12-10 17:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_parser', '0010_kpi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kpi',
            name='content',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
    ]
