# Generated by Django 3.2.15 on 2022-11-02 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0074_socialdisplaysession'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialdisplaysession',
            name='log_file',
            field=models.JSONField(default=dict),
        ),
    ]
