from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0022_apitoken_project_restrictions'),
        ('pentests', '0072_blindtrigramtoken_token_project_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='apitoken', name='is_project_restricted',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='apitoken', name='projects',
            field=models.ManyToManyField(blank=True, related_name='api_tokens', to='pentests.pentestproject'),
        ),
        migrations.AddField(
            model_name='apitoken', name='read_only', field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name='apitoken',
            constraint=models.CheckConstraint(
                condition=models.Q(is_project_restricted=False) | models.Q(admin_permissions_enabled=False),
                name='apitoken_project_no_admin',
            ),
        ),
        migrations.AddConstraint(
            model_name='apitoken',
            constraint=models.CheckConstraint(
                condition=models.Q(read_only=False) | models.Q(is_project_restricted=True),
                name='apitoken_read_only_project',
            ),
        ),
    ]
