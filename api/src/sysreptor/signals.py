from django.db.models.signals import post_delete as django_post_delete
from django.dispatch import Signal

post_create = Signal()
post_finish = Signal()
post_archive = Signal()
post_delete = django_post_delete
post_update = Signal()
post_export = Signal()
post_import = Signal()
