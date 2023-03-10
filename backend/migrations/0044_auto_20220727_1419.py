# Generated by Django 3.0.5 on 2022-07-27 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0043_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='px300',
            field=models.URLField(max_length=400),
        ),
        migrations.AlterField(
            model_name='image',
            name='px64',
            field=models.URLField(max_length=400),
        ),
        migrations.AlterField(
            model_name='image',
            name='px640',
            field=models.URLField(max_length=400),
        ),
    ]
