from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):
    """
    Create database models used by LanguageTool.
    LanguageTool does not come with a way to run migrations, therefore we manage them with the Django ORM.
    Resue Django user accounts for LanguageTool users to authenticate (via a DB view).
    """

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE VIEW users AS " + 
                "SELECT ('x' || translate(u.id::text, '-', ''))::bit(63)::bigint AS id, u.id::text AS email, u.id::text AS api_key FROM users_pentestuser u " +
                "UNION SELECT 1 AS id, 'languagetool' AS email, 'languagetool' AS api_key;",
            reverse_sql="DROP VIEW users;"
        ),
        migrations.CreateModel(
            name='LanguageToolIgnoreWords',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user_id', models.BigIntegerField(db_index=True)),
                ('ignore_word', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_created=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'ignore_words',
            }
        )
    ]
