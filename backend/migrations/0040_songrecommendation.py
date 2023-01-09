# Generated by Django 3.0.5 on 2022-07-26 12:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('backend', '0039_auto_20220720_1432'),
    ]

    operations = [
        migrations.CreateModel(
            name='SongRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('Description', models.CharField(default='', max_length=120)),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Song')),
                ('user_from', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='recommendation_giver', to=settings.AUTH_USER_MODEL)),
                ('user_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_receiver', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]