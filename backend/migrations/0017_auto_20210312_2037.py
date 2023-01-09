# Generated by Django 3.1.1 on 2021-03-12 19:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0016_auto_20201230_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='last_update',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='playlist',
            name='update',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]