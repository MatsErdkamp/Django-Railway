# Generated by Django 3.1.13 on 2022-08-23 15:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0061_auto_20220819_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='SongContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('identifier', models.CharField(max_length=255)),
                ('artist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.artist')),
                ('image', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend.image')),
                ('master_child_album', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='backend.album')),
            ],
        ),
    ]
