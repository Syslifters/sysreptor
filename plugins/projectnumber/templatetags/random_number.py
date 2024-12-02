import random

from django import template

register = template.Library()

@register.simple_tag
def random_number(a, b=None):
    if b is None:
        a, b = 0, a
    return random.randint(int(a), int(b))