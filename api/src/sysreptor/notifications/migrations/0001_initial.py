# Generated by Django 4.1.3 on 2023-01-24 13:11

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import sysreptor.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationSpec',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=sysreptor.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('active_until', models.DateField(blank=True, db_index=True, null=True)),
                ('instance_conditions', models.JSONField(blank=True, default=dict)),
                ('user_conditions', models.JSONField(blank=True, default=dict)),
                ('visible_for_days', models.IntegerField(blank=True, null=True)),
                ('title', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('link_url', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
            bases=(sysreptor.utils.models.ModelDiffMixin, models.Model),
        ),
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=sysreptor.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('visible_until', models.DateTimeField(blank=True, null=True)),
                ('read', models.BooleanField(db_index=True, default=False)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.notificationspec')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'notification')},
            },
            bases=(sysreptor.utils.models.ModelDiffMixin, models.Model),
        ),
    ]
