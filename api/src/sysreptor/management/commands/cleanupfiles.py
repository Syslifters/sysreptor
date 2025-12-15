import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from sysreptor.utils.files import get_all_file_fields


class Command(BaseCommand):
    help = 'Clean up file entries from the DB where the files do not exist on the fielsystem.'

    def file_exists(self, f):
        try:
            with f.open():
                return True
        except Exception:
            return False

    @transaction.atomic
    def handle(self, *args, **options):
        for field_info in get_all_file_fields():
            logging.info(f'Cleaning up {field_info["model"]._meta.label}.{field_info["field_name"]} in storage {field_info["storage_name"]}')
            qs = field_info['model'].objects \
                .filter(pk__in=[
                    o.pk
                    for o in field_info['model'].objects.iterator()
                    if not self.file_exists(getattr(o, field_info['field_name']))
                ])
            if field_info['field'].null:
                qs.update(**{field_info['field_name']: None})
                logging.info(f'  Updated {qs.count()} entries')
            else:
                qs.delete()
                logging.info(f'  Deleted {qs.count()} entries')

