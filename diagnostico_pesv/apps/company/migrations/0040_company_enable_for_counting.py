# Generated by Django 5.1 on 2024-09-09 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0039_remove_company_consultor'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='enable_for_counting',
            field=models.BooleanField(default=False),
        ),
    ]
