# Generated by Django 5.0.6 on 2024-08-06 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0019_driverquestion_vehiclequestions_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fleet',
            name='quantity_employees',
            field=models.IntegerField(default=0),
        ),
    ]