from pathlib import Path
import string


def normalize_filename(name):
    """
    Normalize filename: strip special characters that might conflict with markdown syntax
    """
    out = ''
    for c in name:
        if c in string.ascii_letters + string.digits + '-.':
            out += c
        else:
            out += '-'
    if Path(name).parent.parts:
        out = Path(name).parts[-1]
    if all(map(lambda c: c == '.', out)):
        out = 'file'
    return out
