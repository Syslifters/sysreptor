import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0021_user_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='apitoken',
            name='permissions',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=None,
                null=True,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name='apitoken',
            name='projects',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.UUIDField(),
                blank=True,
                default=None,
                null=True,
                size=None,
            ),
        ),
        migrations.AddConstraint(
            model_name='apitoken',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(('admin_permissions_enabled', False))
                    | (models.Q(('permissions__isnull', True)) & models.Q(('projects__isnull', True)))
                ),
                name='apitoken_restricted_no_admin',
            ),
        ),
        migrations.AddConstraint(
            model_name='apitoken',
            constraint=models.CheckConstraint(
                condition=models.Q(('projects__isnull', True)) | models.Q(('permissions__isnull', False)),
                name='apitoken_projects_requires_permissions',
            ),
        ),
    ]
