# Generated by Django 4.2.4 on 2023-08-07 12:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notificationspec',
            name='instance_conditions',
        ),
    ]
