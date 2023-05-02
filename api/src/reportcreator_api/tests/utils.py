from reportcreator_api.utils.utils import get_key_or_attr


def assertKeysEqual(a, b, keys):
    for k in keys:
        va = get_key_or_attr(a, k)
        vb = get_key_or_attr(b, k)
        assert va == vb, f'Key "{k}" is not equal'

