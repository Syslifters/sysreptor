from django.db.migrations.operations.models import ModelOperation


class AlterModelBaseOperation(ModelOperation):
    reduce_to_sql = False
    reversible = True

    def __init__(self, name, bases, prev_bases):
        self.bases = bases
        self.prev_bases = prev_bases
        super().__init__(name)

    def state_forwards(self, app_label, state):
        state.models[app_label, self.name].bases = self.bases
        state.reload_model(app_label, self.name)

    def state_backwards(self, app_label, state):
        state.models[app_label, self.name].bases = self.prev_bases
        state.reload_model(app_label, self.name)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def describe(self):
        return f"Update {self.name} bases to {self.bases}"

