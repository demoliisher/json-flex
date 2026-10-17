import io
import json as stdlib_json

import json_flex as json


def test_enhanced_writers_are_available():
    text = json.dumps({"name": "张三"}, indent=2, max_depth=1)
    assert "张三" in text

    buffer = io.StringIO()
    assert json.dump({"a": 1}, buffer, indent=2, max_depth=1) is None
    assert buffer.getvalue() == '{\n  "a": 1\n}'


def test_reader_api_comes_from_the_standard_library():
    text = '{"a": [1, 2]}'
    assert json.loads(text) == stdlib_json.loads(text)
    assert json.load(io.StringIO(text)) == stdlib_json.loads(text)
    assert json.JSONDecoder is stdlib_json.JSONDecoder
    assert json.JSONEncoder is stdlib_json.JSONEncoder
    assert json.JSONDecodeError is stdlib_json.JSONDecodeError


def test_extra_attributes_are_forwarded():
    assert json.encoder is stdlib_json.encoder
    assert json.decoder is stdlib_json.decoder
    assert json.scanner is stdlib_json.scanner
    assert json.detect_encoding(b'{"a": 1}') == "utf-8"
    assert "loads" in dir(json)


def test_alias_does_not_patch_the_standard_library():
    assert stdlib_json.dumps({"a": 1}) == '{"a": 1}'


def test_all_contains_the_combined_api():
    assert set(json.__all__) == {
        "JSONDecodeError",
        "JSONDecoder",
        "JSONEncoder",
        "dump",
        "dumps",
        "load",
        "loads",
    }


def test_round_trip_through_the_alias():
    data = {"a": [1, 2], "name": "张三"}
    assert json.loads(json.dumps(data, indent=2, max_depth=1)) == data
