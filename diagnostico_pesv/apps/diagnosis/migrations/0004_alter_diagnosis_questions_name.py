# Generated by Django 5.0.6 on 2024-07-15 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0003_alter_diagnosis_questions_cycle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnosis_questions',
            name='name',
            field=models.TextField(default=None, null=True),
        ),
    ]
