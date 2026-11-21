"""Small demonstration behavior; not a framework dependency."""
def normalize_label(value):
    if not isinstance(value, str):
        raise TypeError('label must be text')
    result = ' '.join(value.split())
    if not result:
        raise ValueError('label must not be empty')
    return result
