# Generated by Django 4.0.6 on 2022-08-21 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consumptions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consumption',
            name='deprecated',
            field=models.BooleanField(default=False),
        ),
    ]
