# Generated by Django 5.1 on 2024-08-20 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0039_remove_company_consultor'),
        ('corporate_group', '0003_remove_corporate_company_remove_corporate_diagnosis_and_more'),
        ('diagnosis', '0028_diagnosis_observation'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CorporateCompanyDiagnosis',
            new_name='Corporate_Company_Diagnosis',
        ),
    ]
