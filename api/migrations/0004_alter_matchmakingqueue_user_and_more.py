# Generated by Django 5.1.3 on 2024-12-04 10:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_matchmakingqueue_time_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchmakingqueue',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matchmaking_queue_entries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='matchmakingqueue',
            constraint=models.UniqueConstraint(fields=('user', 'time_limit'), name='unique_user_time_limit'),
        ),
    ]