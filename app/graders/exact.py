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


def structure_metrics(case, output):
    """Check the key/type contract represented by this case's expected JSON."""
    try:
        actual = json.loads(output)
    except (ValueError, TypeError):
        actual = None
    expected = case.expected

    def shape(value, example):
        if case.dataset_version == "analytical-v1" and type(example) in (float, int):
            return type(value) in (float, int)
        if type(value) is not type(example):
            return False
        if isinstance(example, dict):
            return value.keys() == example.keys() and all(shape(value[k], v) for k, v in example.items())
        if isinstance(example, list):
            return len(value) == len(example) and all(shape(a, b) for a, b in zip(value, example))
        return True

    metrics = {"schema_valid": shape(actual, expected)}
    if case.task_type == "structured_extraction" and isinstance(expected, dict):
        fields = actual if isinstance(actual, dict) else {}
        correct = sum(k in fields and shape(fields[k], v) and fields[k] == v for k, v in expected.items())
        metrics["field_counts"] = [correct, len(fields), len(expected)]
    return metrics
