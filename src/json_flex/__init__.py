import json as _json
from json import JSONDecodeError, JSONDecoder, JSONEncoder, load, loads
from typing import Any

from ._format import dump, dumps

__all__ = [
    "JSONDecodeError",
    "JSONDecoder",
    "JSONEncoder",
    "dump",
    "dumps",
    "load",
    "loads",
]
__version__ = "1.0.0"


def __getattr__(name: str) -> Any:
    return getattr(_json, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_json)))
