# Generated by Django 3.0.5 on 2022-08-14 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0047_profile_banner_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='stream',
            name='imported',
            field=models.BooleanField(default=False),
        ),
    ]
