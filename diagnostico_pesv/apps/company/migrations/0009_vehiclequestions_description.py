# Generated by Django 5.0.6 on 2024-07-10 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0008_driverquestion_vehiclequestions_driver_fleet'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiclequestions',
            name='description',
            field=models.TextField(null=True),
        ),
    ]