# Generated by Django 3.2.15 on 2022-11-03 19:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0080_socialdisplayuserlog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialdisplaysession',
            name='active',
        ),
        migrations.RemoveField(
            model_name='socialdisplaysession',
            name='active_session_duration',
        ),
    ]
