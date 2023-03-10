# Generated by Django 3.1 on 2022-08-19 12:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0060_auto_20220819_1402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='album_container',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.albumcontainer'),
        ),
        migrations.AlterField(
            model_name='album',
            name='image',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.image'),
        ),
        migrations.AlterField(
            model_name='albumcontainer',
            name='image',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.image'),
        ),
        migrations.AlterField(
            model_name='playlist',
            name='image',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.image'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.image'),
        ),
        migrations.AlterField(
            model_name='songrecommendation',
            name='user_from',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recommendation_sender', to=settings.AUTH_USER_MODEL),
        ),
    ]
