# json-flex

Readable JSON with depth-limited indentation and compact leaf lists.

`json-flex` keeps the outer structure of a document easy to scan and collapses
the deeper parts onto single lines. It supports the same serialization options
as Python's `json` module while giving you control over how much of the
document is expanded.

## Features

- Expand only the outer layers with `max_depth`.
- Keep flat lists of scalars on one line with `compact_leaf`.
- Use `sort_keys`, `default`, `cls`, `skipkeys`, `separators`, and other
  `json.dumps` options as usual.
- Keep non-ASCII text readable by default.
- No runtime dependencies.

## Installation

Requires Python 3.9 or newer.

```bash
pip install json-flex
```

If the package is not on PyPI yet, install it from a checkout:

```bash
pip install .
```

## Quick start

```python
from json_flex import dumps

data = {
    "request": {"id": "req-42", "user": {"name": "Ada", "roles": ["admin", "dev"]}},
    "items": [
        {"sku": "A-1", "qty": 2, "price": 9.5},
        {"sku": "B-7", "qty": 1, "price": 3.0},
    ],
}

print(dumps(data, indent=2, max_depth=1))
```

Output:

```json
{
  "request": {"id": "req-42", "user": {"name": "Ada", "roles": ["admin", "dev"]}},
  "items": [{"sku": "A-1", "qty": 2, "price": 9.5}, {"sku": "B-7", "qty": 1, "price": 3.0}]
}
```

The top-level fields stay visible. Everything below them is kept on one line.

## Choosing a depth

`max_depth` counts the root container as level 1.

- `max_depth=1` (default): expand the root and collapse everything inside it.
- `max_depth=2`: expand the root and its direct children.
- `max_depth=None`: expand every container.
- `max_depth` must be a positive integer or `None`. Other types raise
  `TypeError`; values below 1 raise `ValueError`. Use `indent=None` for fully
  compact output.

For this data:

```python
data = {"a": {"b": {"c": 1}}, "values": [1, 2, 3]}
```

`max_depth=1`:

```json
{
  "a": {"b": {"c": 1}},
  "values": [1, 2, 3]
}
```

`max_depth=2`:

```json
{
  "a": {
    "b": {"c": 1}
  },
  "values": [
    1,
    2,
    3
  ]
}
```

`max_depth=None`:

```json
{
  "a": {
    "b": {
      "c": 1
    }
  },
  "values": [
    1,
    2,
    3
  ]
}
```

## Keeping flat lists inline

A leaf list is a list whose items are all scalars or empty containers.
`compact_leaf=True` keeps such lists on one line, regardless of `max_depth`.

```python
print(dumps(data, indent=2, max_depth=None, compact_leaf=True))
```

```json
{
  "a": {
    "b": {
      "c": 1
    }
  },
  "values": [1, 2, 3]
}
```

Lists that contain non-empty objects or lists are not affected by
`compact_leaf`; their layout follows `max_depth`.

## Non-ASCII text

Unlike `json.dumps`, `json-flex` defaults to `ensure_ascii=False`, so text stays
readable:

```python
print(dumps({"name": "张三"}, indent=2, max_depth=None))
```

```json
{
  "name": "张三"
}
```

Pass `ensure_ascii=True` when the output must be pure ASCII:

```python
print(dumps({"name": "张三"}, indent=2, max_depth=None, ensure_ascii=True))
```

```json
{
  "name": "\u5f20\u4e09"
}
```

When writing to a file, open it with UTF-8 encoding.

## Writing to a file

`dump` takes the same options as `dumps` and writes to a text stream:

```python
from json_flex import dump

with open("report.json", "w", encoding="utf-8") as fp:
    dump(data, fp, indent=2, max_depth=2)
```

## Using it as the `json` module (optional)

When a file needs formatted output and the standard reader API in one place,
the package can be imported under the `json` name:

```python
import json_flex as json

payload = json.loads(raw_text)
print(json.dumps(payload, max_depth=2))
```

`dumps` and `dump` are the enhanced writers. `loads`, `load`, `JSONEncoder`,
`JSONDecoder`, and `JSONDecodeError` come from the standard library, and other
attributes such as `detect_encoding` are forwarded.

This alias only affects the current module. It does not replace the global
`json` module, so other modules that use `import json` keep the standard
behavior.

The defaults differ from `json.dumps`: `indent=4`, `ensure_ascii=False`, and
`max_depth=1`. Pass `indent=None` and `ensure_ascii=True` when you need the
standard library's compact ASCII output.

For library code, prefer `from json_flex import dumps` so the enhanced writer is
explicit.

## API

| Function | Description |
| --- | --- |
| `dumps(obj, *, indent=4, max_depth=1, compact_leaf=False, ensure_ascii=False, **json_kwargs)` | Returns the formatted JSON string. |
| `dump(obj, fp, *, indent=4, max_depth=1, compact_leaf=False, ensure_ascii=False, **json_kwargs)` | Writes the formatted result to a text stream. |

Parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `obj` | required | Object to serialize. |
| `fp` | required for `dump` | Text stream to write to. |
| `indent` | `4` | Number of spaces or a custom indentation string. `None` returns compact output. |
| `max_depth` | `1` | Number of container levels to expand. The root counts as level 1. `None` expands every level. |
| `compact_leaf` | `False` | Keep lists of scalars and empty containers on one line. Takes priority over `max_depth`. |
| `ensure_ascii` | `False` | Escape non-ASCII characters when `True`. |
| `**json_kwargs` | | Additional options passed to `json.dumps`, such as `sort_keys`, `separators`, `default`, `cls`, `skipkeys`, and `allow_nan`. |

## Differences from `json.dumps`

- `ensure_ascii` defaults to `False`.
- `max_depth` and `compact_leaf` are available.
- `indent` defaults to `4` instead of `None`.
- All formatting options are keyword-only.

Serialization of values, keys, and errors follows the standard library's `json`
module.

## License

MIT. See [LICENSE](LICENSE).
