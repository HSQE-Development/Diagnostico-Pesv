# Generated by Django 5.0.6 on 2024-07-05 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sign', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cedula',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]