# Generated by Django 5.0.6 on 2024-07-15 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0023_company_diagnosis_step'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='diagnosis_step',
            field=models.IntegerField(default=1),
        ),
    ]
