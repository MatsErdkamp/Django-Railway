# Generated by Django 3.2.15 on 2022-12-17 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0089_songcontainer_uri'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenreContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=64, unique=True)),
                ('subgenres', models.ManyToManyField(to='backend.Genre')),
            ],
        ),
    ]
