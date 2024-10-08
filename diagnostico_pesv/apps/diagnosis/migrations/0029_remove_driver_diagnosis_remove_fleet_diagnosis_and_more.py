# Generated by Django 5.1 on 2024-08-22 17:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0039_remove_company_consultor'),
        ('diagnosis', '0028_diagnosis_observation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver',
            name='diagnosis',
        ),
        migrations.RemoveField(
            model_name='fleet',
            name='diagnosis',
        ),
        migrations.AlterField(
            model_name='driver',
            name='driver_question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='diagnosis.driverquestion'),
        ),
        migrations.CreateModel(
            name='Diagnosis_Counter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted_at')),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_counter', to='company.company')),
                ('diagnosis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diagnosis.diagnosis')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='driver',
            name='diagnosis_counter',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='diagnosis.diagnosis_counter'),
        ),
        migrations.AddField(
            model_name='fleet',
            name='diagnosis_counter',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='diagnosis.diagnosis_counter'),
        ),
    ]
