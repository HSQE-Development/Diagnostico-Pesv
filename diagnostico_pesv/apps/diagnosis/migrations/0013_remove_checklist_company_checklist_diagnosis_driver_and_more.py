# Generated by Django 5.0.6 on 2024-07-31 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0036_remove_fleet_company_remove_fleet_vehicle_question_and_more'),
        ('diagnosis', '0012_diagnosis'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checklist',
            name='company',
        ),
        migrations.AddField(
            model_name='checklist',
            name='diagnosis',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='diagnosis.diagnosis'),
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted_at')),
                ('quantity', models.IntegerField(default=0)),
                ('diagnosis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diagnosis.diagnosis')),
                ('driver_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.driverquestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Fleet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted_at')),
                ('quantity_owned', models.IntegerField(default=0)),
                ('quantity_third_party', models.IntegerField(default=0)),
                ('quantity_arrended', models.IntegerField(default=0)),
                ('quantity_contractors', models.IntegerField(default=0)),
                ('quantity_intermediation', models.IntegerField(default=0)),
                ('quantity_leasing', models.IntegerField(default=0)),
                ('quantity_renting', models.IntegerField(default=0)),
                ('diagnosis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diagnosis.diagnosis')),
                ('vehicle_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.vehiclequestions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
