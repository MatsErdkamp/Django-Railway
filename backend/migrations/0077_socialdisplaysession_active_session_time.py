# Generated by Django 3.2.15 on 2022-11-03 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0076_alter_socialdisplaysession_log_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialdisplaysession',
            name='active_session_time',
            field=models.FloatField(default=1.0),
        ),
    ]
