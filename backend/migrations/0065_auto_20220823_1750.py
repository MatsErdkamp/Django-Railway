# Generated by Django 3.1.13 on 2022-08-23 15:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0064_song_song_container'),
    ]

    operations = [
        migrations.AlterField(
            model_name='songcontainer',
            name='master_child_song',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='backend.song'),
        ),
    ]
