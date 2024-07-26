# Generated by Django 5.0.6 on 2024-07-22 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis_requirement', '0002_alter_diagnosis_requirement_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosis_requirement',
            name='advanced',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diagnosis_requirement',
            name='basic',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diagnosis_requirement',
            name='standard',
            field=models.BooleanField(default=False),
        ),
    ]