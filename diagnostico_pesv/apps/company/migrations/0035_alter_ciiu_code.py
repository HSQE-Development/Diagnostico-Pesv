# Generated by Django 5.0.6 on 2024-07-29 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0034_company_ciius_delete_companyciiu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ciiu',
            name='code',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
    ]
