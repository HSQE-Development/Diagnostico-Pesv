# Generated by Django 5.1 on 2024-08-28 18:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corporate_group', '0006_corporate_companies_corporate_diagnoses_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corporate',
            name='diagnoses',
        ),
        migrations.RemoveField(
            model_name='corporate_company_diagnosis',
            name='diagnosis',
        ),
    ]