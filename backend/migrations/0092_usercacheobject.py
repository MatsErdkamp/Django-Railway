# Generated by Django 3.2.15 on 2022-12-29 17:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0091_auto_20221221_1721'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCacheObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default=None, max_length=128, unique=True)),
                ('cache_type', models.CharField(choices=[('songs', 'songs'), ('artists', 'artists'), ('albums', 'albums')], default='undefined', max_length=16)),
                ('sort_mode', models.CharField(choices=[('streams', 'streams'), ('compatibility', 'compatibility')], default='undefined', max_length=16)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
