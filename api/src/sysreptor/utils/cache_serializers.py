import json

from django.core.serializers.json import DjangoJSONEncoder


class JsonRedisSerializer:
    def dumps(self, obj):
        # Keep incr()/decr() atomicity like Django's RedisSerializer.
        if type(obj) is int:
            return obj
        return json.dumps(obj, cls=DjangoJSONEncoder).encode()

    def loads(self, data):
        try:
            return int(data)
        except (ValueError, TypeError):
            return json.loads(data)
