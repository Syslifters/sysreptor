import uuid

import django.core.serializers.json
import django.db.models.deletion
from django.db import migrations, models

import sysreptor.utils.crypto.fields
import sysreptor.utils.models


def delete_old_checkpoints(apps, schema_editor):
    # Temporary chat state; safer to wipe than convert the old single-blob format.
    LangchainCheckpoint = apps.get_model('ai', 'LangchainCheckpoint')
    ChatThread = apps.get_model('ai', 'ChatThread')
    LangchainCheckpoint.objects.all().delete()
    ChatThread.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(delete_old_checkpoints, migrations.RunPython.noop),
        migrations.CreateModel(
            name='LangchainCheckpointBlob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=sysreptor.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('checkpoint_ns', models.CharField(db_index=True, default='', max_length=255)),
                ('channel', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('blob', sysreptor.utils.crypto.fields.EncryptedField(base_field=models.BinaryField(), blank=True, editable=True, null=True)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkpoint_blobs', to='ai.chatthread')),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
                'unique_together': {('thread', 'checkpoint_ns', 'channel', 'version')},
            },
        ),
        migrations.CreateModel(
            name='LangchainCheckpointWrite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=sysreptor.utils.models.now, editable=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('checkpoint_ns', models.CharField(db_index=True, default='', max_length=255)),
                ('checkpoint_id', models.UUIDField()),
                ('task_id', models.CharField(max_length=255)),
                ('task_path', models.CharField(blank=True, default='', max_length=1024)),
                ('idx', models.IntegerField()),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('blob', sysreptor.utils.crypto.fields.EncryptedField(base_field=models.BinaryField(), editable=True)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checkpoint_writes', to='ai.chatthread')),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
                'unique_together': {('thread', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx')},
            },
        ),
        migrations.AddIndex(
            model_name='langchaincheckpointwrite',
            index=models.Index(fields=['thread', 'checkpoint_ns', 'checkpoint_id'], name='ai_langchai_thread__7c1a2b_idx'),
        ),
        migrations.RemoveField(
            model_name='langchaincheckpoint',
            name='checkpoint',
        ),
        migrations.RemoveField(
            model_name='langchaincheckpoint',
            name='checkpoint_type',
        ),
        migrations.RemoveField(
            model_name='langchaincheckpoint',
            name='pending_writes',
        ),
        migrations.RemoveField(
            model_name='langchaincheckpoint',
            name='pending_writes_type',
        ),
        migrations.AddField(
            model_name='langchaincheckpoint',
            name='checkpoint',
            field=sysreptor.utils.crypto.fields.EncryptedField(
                base_field=models.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
                default=dict,
                editable=True,
            ),
        ),
        migrations.AlterField(
            model_name='langchaincheckpoint',
            name='metadata',
            field=sysreptor.utils.crypto.fields.EncryptedField(base_field=models.BinaryField(), blank=True, default=b'{}', editable=True),
        ),
    ]
