# Generated by Django 3.2.15 on 2022-12-30 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0095_auto_20221230_1356'),
    ]

    operations = [
        migrations.RenameField(
            model_name='groupcacheobject',
            old_name='invalidated_subcache_amount',
            new_name='invalidated_subcache_percentage',
        ),
        migrations.AddField(
            model_name='groupcacheobject',
            name='valid_subcaches',
            field=models.ManyToManyField(to='backend.UserCacheObject'),
        ),
    ]
