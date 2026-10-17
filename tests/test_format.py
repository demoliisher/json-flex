import io
import json
import sys

import pytest

from json_flex import dump, dumps

DATA = {
    "name": "Alice",
    "age": 30,
    "active": True,
    "score": None,
    "address": {
        "city": "New York",
        "zip": 10001,
        "coordinates": [40.7128, -74.0060],
    },
    "hobbies": ["reading", "cycling", {"indoor": "chess", "outdoor": "hiking"}],
    "matrix": [[1, 2], [3, 4]],
    "empty_list": [],
    "empty_dict": {},
    "tuple_data": [1, "two", 3.0],
    "nested_tuples": [[1, 2], [3, 4]],
}


@pytest.mark.parametrize("indent", [2, 4, "\t", 0, ""])
def test_unlimited_depth_matches_stdlib(indent):
    assert dumps(DATA, indent=indent, max_depth=None) == json.dumps(DATA, indent=indent)


@pytest.mark.parametrize("indent", [2, 4, "\t", 0, ""])
def test_deep_depth_matches_stdlib(indent):
    # A max_depth deeper than the data forces a line-by-line rebuild identical to stdlib.
    assert dumps(DATA, indent=indent, max_depth=100) == json.dumps(DATA, indent=indent)


@pytest.mark.parametrize(
    "separators",
    [(",", ":"), (", ", ": "), ("", ":")],
)
def test_unlimited_depth_matches_stdlib_with_separators(separators):
    expected = json.dumps(DATA, indent=2, separators=separators)
    assert dumps(DATA, indent=2, max_depth=None, separators=separators) == expected
    assert dumps(DATA, indent=2, max_depth=100, separators=separators) == expected


def test_depth_one_expands_only_root():
    text = dumps(DATA, indent=4, max_depth=1, compact_leaf=False)
    assert json.loads(text) == DATA
    assert '"address": {"city": "New York", "zip": 10001, "coordinates": [40.7128, -74.006]}' in text
    assert '"hobbies": ["reading", "cycling", {"indoor": "chess", "outdoor": "hiking"}]' in text
    assert '"matrix": [[1, 2], [3, 4]]' in text


def test_depth_two_expands_second_level():
    text = dumps(DATA, indent=2, max_depth=2, compact_leaf=False)
    assert json.loads(text) == DATA
    assert (
        '"address": {\n    "city": "New York",\n    "zip": 10001,\n    "coordinates": [40.7128, -74.006]\n  }' in text
    )
    assert '"matrix": [\n    [1, 2],\n    [3, 4]\n  ]' in text


def test_compact_leaf_has_priority_over_max_depth():
    text = dumps(DATA, indent=2, max_depth=None, compact_leaf=True)
    assert json.loads(text) == DATA
    assert '"coordinates": [40.7128, -74.006]' in text
    assert '"tuple_data": [1, "two", 3.0]' in text
    assert '"nested_tuples": [\n    [1, 2],\n    [3, 4]\n  ]' in text


def test_compact_leaf_applies_at_any_depth():
    obj = {"outer": {"inner": {"nums": [1, 2, 3]}}}
    text = dumps(obj, indent=2, max_depth=None, compact_leaf=True)
    assert '"nums": [1, 2, 3]' in text


def test_compact_leaf_on_root_list():
    assert dumps([1, 2], indent=2, max_depth=None, compact_leaf=True) == "[1, 2]"


def test_tuples_are_serialized_as_arrays():
    obj = {"point": (1, 2), "groups": ((3, 4), (5, 6))}
    text = dumps(obj, indent=2, max_depth=None, compact_leaf=True)
    assert json.loads(text) == {"point": [1, 2], "groups": [[3, 4], [5, 6]]}
    assert '"point": [1, 2]' in text


def test_compact_leaf_keeps_empty_containers_inline():
    assert dumps([{}, []], indent=2, max_depth=None, compact_leaf=True) == "[{}, []]"


def test_compact_leaf_does_not_compact_nested_list():
    text = dumps([{"a": 1}], indent=2, max_depth=None, compact_leaf=True)
    assert text == '[\n  {\n    "a": 1\n  }\n]'


def test_unicode_line_separators_are_not_split():
    obj = {"text": "line separator end"}  # noqa: RUF001
    expected = json.dumps(obj, indent=2, ensure_ascii=False)
    assert dumps(obj, indent=2, max_depth=100, ensure_ascii=False) == expected


def test_options_are_keyword_only():
    with pytest.raises(TypeError):
        dumps(DATA, 2)


def test_empty_containers():
    assert dumps({}, indent=2, max_depth=None) == "{}"
    assert dumps([], indent=2, max_depth=None) == "[]"


def test_scalars():
    assert dumps(123, indent=2) == "123"
    assert dumps("hello", indent=2) == '"hello"'
    assert dumps(None, indent=2) == "null"


def test_indent_none_returns_compact():
    text = dumps(DATA, indent=None, max_depth=5)
    assert "\n" not in text
    assert json.loads(text) == DATA


@pytest.mark.parametrize("key", [1, 1.5, True, None])
def test_non_string_keys_match_stdlib(key):
    obj = {key: "value"}
    assert dumps(obj, indent=2, max_depth=1) == json.dumps(obj, indent=2)


def test_skipkeys_is_honoured():
    assert dumps({(1, 2): 3}, indent=2, max_depth=1, skipkeys=True) == "{}"
    nested = {"a": {(1, 2): 3}}
    assert json.loads(dumps(nested, indent=2, max_depth=1, skipkeys=True)) == {"a": {}}


def test_separators_apply_to_collapsed_containers():
    text = dumps({"a": [1, 2], "b": {"c": 4}}, indent=2, max_depth=1, separators=(",", ":"))
    assert text == '{\n  "a":[1,2],\n  "b":{"c":4}\n}'


def test_sort_keys_matches_stdlib():
    obj = {"b": 1, "a": {"d": 2, "c": 3}}
    assert dumps(obj, indent=2, max_depth=100, sort_keys=True) == json.dumps(obj, indent=2, sort_keys=True)


def test_ensure_ascii_false():
    obj = {"中文": "值"}
    assert dumps(obj, indent=2, max_depth=100, ensure_ascii=False) == json.dumps(obj, indent=2, ensure_ascii=False)


def test_ensure_ascii_defaults_to_false():
    obj = {"中文": "值"}
    assert "中文" in dumps(obj, indent=2, max_depth=None)
    assert "\\u4e2d\\u6587" in dumps(obj, indent=2, max_depth=None, ensure_ascii=True)


def test_default_parameter():
    class Point:
        pass

    text = dumps({"p": Point()}, indent=2, max_depth=100, default=lambda _: "point")
    assert json.loads(text) == {"p": "point"}


def test_custom_encoder_class():
    class ComplexEncoder(json.JSONEncoder):
        def default(self, value):
            if isinstance(value, complex):
                return [value.real, value.imag]
            return super().default(value)

    text = dumps({"z": 1 + 2j}, indent=2, max_depth=1, cls=ComplexEncoder)
    assert json.loads(text) == {"z": [1.0, 2.0]}


def test_custom_encoder_is_applied_to_whole_object():
    class FixedEncoder(json.JSONEncoder):
        def iterencode(self, value, _one_shot=False):
            return ['{"fixed": true}']

    obj = {"a": 1}
    expected = json.dumps(obj, cls=FixedEncoder)
    assert dumps(obj, indent=2, max_depth=1, cls=FixedEncoder) == expected


def test_circular_reference_is_detected():
    obj = {}
    obj["self"] = obj
    for max_depth in (None, 1, 5):
        with pytest.raises(ValueError, match="Circular reference"):
            dumps(obj, indent=2, max_depth=max_depth)


def test_deep_nesting_does_not_recurse_in_formatter():
    root = {}
    node = root
    for _ in range(1200):
        node["a"] = {}
        node = node["a"]

    # The standard-library encoder is recursive too; raise its limit to test the formatter itself.
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    try:
        assert dumps(root, indent=2, max_depth=None) == json.dumps(root, indent=2)
        assert dumps(root, indent=2, max_depth=2000) == json.dumps(root, indent=2)
        collapsed = dumps(root, indent=2, max_depth=1)
    finally:
        sys.setrecursionlimit(old_limit)
    assert collapsed.startswith('{\n  "a": ')
    assert collapsed.endswith("\n}")


def test_invalid_indent_type_is_rejected():
    with pytest.raises(TypeError):
        dumps({"a": 1}, indent=2.5)


@pytest.mark.parametrize("value", [0, -1])
def test_max_depth_must_be_positive(value):
    with pytest.raises(ValueError, match="max_depth"):
        dumps({"a": 1}, max_depth=value)


@pytest.mark.parametrize("value", [1.5, "2"])
def test_max_depth_must_be_an_int(value):
    with pytest.raises(TypeError, match="max_depth"):
        dumps({"a": 1}, max_depth=value)


def test_dump_writes_same_text_as_dumps():
    buffer = io.StringIO()
    assert dump(DATA, buffer, indent=2, max_depth=1) is None
    assert buffer.getvalue() == dumps(DATA, indent=2, max_depth=1)


def test_dump_writes_utf8_file(tmp_path):
    path = tmp_path / "output.json"
    with path.open("w", encoding="utf-8") as fp:
        dump({"中文": "值"}, fp, indent=2, max_depth=None)
    assert json.loads(path.read_text(encoding="utf-8")) == {"中文": "值"}


def test_newline_in_separators_is_rejected():
    with pytest.raises(ValueError, match="separators"):
        dumps({"a": 1}, indent=2, separators=(",\n", ": "))


def test_newline_in_indent_is_rejected():
    with pytest.raises(ValueError, match="indent"):
        dumps({"a": 1}, indent="\n")
