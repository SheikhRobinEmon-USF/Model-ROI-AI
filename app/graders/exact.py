import json

def grade(case, output):
    """Explicit types matter: JSON true must not equal numeric 1."""
    try:
        actual = json.loads(output)
    except (ValueError, TypeError):
        return {'passed':False,'reason':'invalid_json'}
    expected = case.expected
    def same(a,b):
        if case.dataset_version == "analytical-v1" and type(a) in (int, float) and type(b) in (int, float):
            return a == b
        if type(a) is not type(b):
            return False
        if isinstance(a,dict):
            return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
        if isinstance(a,list):
            return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        return a==b
    passed = same(actual,expected)
    return {'passed':passed,'reason':'exact_match' if passed else 'field_or_type_mismatch'}
