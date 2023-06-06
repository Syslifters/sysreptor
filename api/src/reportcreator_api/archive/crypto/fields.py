import io
import json

import elasticapm
from django.db import models
from django.core import checks

from reportcreator_api.archive.crypto import base as crypto


class EncryptedField(models.BinaryField):
    def __init__(self, base_field, editable=True, *args, **kwargs) -> None:
        self.base_field = base_field
        super().__init__(editable=editable, *args, **kwargs)
    
    @property
    def model(self):
        try:
            return self.__dict__["model"]
        except KeyError:
            raise AttributeError(
                "'%s' object has no attribute 'model'" % self.__class__.__name__
            )

    @model.setter
    def model(self, model):
        self.__dict__["model"] = model
        self.base_field.model = model

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        if self.base_field.remote_field:
            errors.append(
                checks.Error(
                    "Base field for EncryptedField cannot be a related field.",
                    obj=self,
                )
            )
        else:
            # Remove the field name checks as they are not needed here.
            base_errors = self.base_field.check()
            if base_errors:
                messages = "\n    ".join(
                    "%s (%s)" % (error.msg, error.id) for error in base_errors
                )
                errors.append(
                    checks.Error(
                        "Base field for EncryptedField has errors:\n    %s" % messages,
                        obj=self,
                    )
                )
        return errors

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.base_field.set_attributes_from_name(name)

    @property
    def description(self):
        return 'Encrypted ' + self.base_field.description
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({
            "base_field": self.base_field.clone(),
        })
        return name, path, args, kwargs
    
    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return value
        
        if isinstance(self.base_field, models.JSONField):
            value = json.dumps(value, cls=self.base_field.encoder).encode()
        elif isinstance(self.base_field, models.BinaryField):
            pass
        else:
            value = self.base_field.get_db_prep_value(value=value, connection=connection, prepared=prepared)
            if isinstance(value, bytes):
                pass
            elif isinstance(value, str):
                value = value.encode()
            else:
                value = str(value).encode()

        enc = io.BytesIO()
        with crypto.open(fileobj=enc, mode='wb') as c:
            c.write(value)
        value = enc.getvalue()

        return super().get_db_prep_value(value=value, connection=connection, prepared=prepared)

    def from_db_value(self, value, expression, connection):
        value = super().to_python(value)

        if isinstance(value, (bytes, memoryview)):
            with crypto.open(fileobj=io.BytesIO(value), mode='rb') as c:
                value = crypto.readall(c)
            if not isinstance(self.base_field, models.BinaryField):
                value = value.decode()
        if hasattr(self.base_field, 'from_db_value'):
            value = self.base_field.from_db_value(value=value, expression=expression, connection=connection)
        return self.base_field.to_python(value)
    
    def to_python(self, value):
        return self.base_field.to_python(value)
    
    def value_to_string(self, obj):
        return self.base_field.value_to_string(obj)

    def value_from_object(self, obj):
        return self.base_field.value_from_object(obj)
    
    def formfield(self, **kwargs):
        return self.base_field.formfield(**kwargs)

    def has_default(self) -> bool:
        return self.base_field.has_default()

    def get_default(self):
        return self.base_field.get_default()

