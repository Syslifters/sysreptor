from django.db import models


class LanguageToolIgnoreWords(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_created=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.BigIntegerField(db_index=True)
    ignore_word = models.CharField(max_length=255)

    class Meta:
        db_table = 'ignore_words'

