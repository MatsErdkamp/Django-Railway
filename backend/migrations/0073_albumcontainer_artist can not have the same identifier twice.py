# Generated by Django 3.2.15 on 2022-11-02 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0072_merge_20220906_1152'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='albumcontainer',
            constraint=models.UniqueConstraint(fields=('album_type', 'artist', 'identifier'), name='Artist can not have the same identifier twice'),
        ),
    ]
