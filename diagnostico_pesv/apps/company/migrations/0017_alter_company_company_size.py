# Generated by Django 5.0.6 on 2024-07-12 13:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0016_alter_company_company_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='company_size',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='company.companysize'),
        ),
    ]
