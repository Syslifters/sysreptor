from channels_postgres.core import PostgresChannelLayer
from channels_postgres.db import DatabaseLayer

from reportcreator_api.utils.utils import omit_keys


class CustomizedPostgresChannelLayer(PostgresChannelLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove incompatible options
        self.db_params = omit_keys(self.db_params, ['context', 'cursor_factory'])
        self.django_db = DatabaseLayer(using='default', logger=self.logger)
