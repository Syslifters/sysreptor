from reportcreator_api.utils.utils import get_key_or_attr


class TestHelperMixin:
    def assertKeysEqual(self, a, b, keys):
        for k in keys:
            va = get_key_or_attr(a, k)
            vb = get_key_or_attr(b, k)
            self.assertEqual(va, vb, msg=f'Key "{k}" is not equal')
        
    