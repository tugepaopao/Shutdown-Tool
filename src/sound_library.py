"""Public edition: user-selected audio only; old builtin tokens resolve to no file."""
def resolve(path):
    value = (path or '').strip().strip('"')
    return '' if value.startswith('builtin:') else value
