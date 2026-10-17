import json
from typing import Any, Optional, TextIO, Union

__all__ = ["dump", "dumps"]

_CLOSING = {"{": "}", "[": "]"}


class _Container:
    __slots__ = ("items", "opening", "prefix")

    def __init__(self, prefix: str, opening: str, items: list[Any]) -> None:
        self.prefix = prefix
        self.opening = opening
        self.items = items


class _Reformatter:
    def __init__(
        self,
        indent_unit: str,
        pretty_item_sep: str,
        inline_item_sep: str,
        max_depth: Optional[int],
        compact_leaf: bool,
    ) -> None:
        self.indent_unit = indent_unit
        self.pretty_item_sep = pretty_item_sep
        self.inline_item_sep = inline_item_sep
        self.max_depth = max_depth
        self.compact_leaf = compact_leaf
        self.lines: list[str] = []

    def reformat(self, text: str) -> str:
        if "\n" not in text:
            return text

        # JSON escapes newlines inside strings, so splitting on \n never cuts a value.
        self.lines = text.split("\n")
        root = self._parse_tree()
        if not root.items or self._should_collapse(root, 0):
            return self._inline(root)
        return "\n".join(self._render(root))

    def _parse_tree(self) -> _Container:
        # An explicit stack keeps deeply nested input from hitting the recursion limit.
        first = self.lines[0]
        opening = first[-1:]
        if opening not in _CLOSING:
            raise ValueError("Unrecognized JSON layout: the first line does not open a container.")
        root = _Container(first[:-1], opening, [])
        stack = [root]
        index = 1

        while stack:
            if index >= len(self.lines):
                raise ValueError("Unrecognized JSON layout: the container is not closed.")
            # CPython 3.12 leaves a whitespace-only container when all keys are skipped.
            if not self.lines[index].strip():
                index += 1
                continue
            node = stack[-1]
            depth = len(stack) - 1

            raw = self._strip_sep(self._strip_indent(self.lines[index], depth))
            close = _CLOSING[node.opening]
            if raw == close:
                stack.pop()
                index += 1
                continue

            item = self._strip_sep(self._strip_indent(self.lines[index], depth + 1))
            if not item:
                raise ValueError("Unrecognized JSON layout: empty item.")
            if item[-1] in _CLOSING:
                child = _Container(item[:-1], item[-1], [])
                node.items.append(child)
                stack.append(child)
            else:
                node.items.append(item)
            index += 1

        if index != len(self.lines):
            raise ValueError("Unrecognized JSON layout: unexpected trailing lines.")
        return root

    def _strip_indent(self, line: str, depth: int) -> str:
        prefix = self.indent_unit * depth
        if not prefix:
            return line
        if not line.startswith(prefix):
            raise ValueError("Unrecognized JSON layout: indentation does not match the indent argument.")
        return line[len(prefix) :]

    def _strip_sep(self, content: str) -> str:
        if self.pretty_item_sep and content.endswith(self.pretty_item_sep):
            return content[: -len(self.pretty_item_sep)]
        return content

    def _should_collapse(self, node: _Container, depth: int) -> bool:
        if self.max_depth is not None and depth >= self.max_depth:
            return True
        if self.compact_leaf and node.opening == "[":
            return all(isinstance(item, str) for item in node.items)
        return False

    def _inline(self, root: _Container) -> str:
        parts: list[str] = []
        stack: list[Any] = [root]

        while stack:
            current = stack.pop()
            if isinstance(current, str):
                parts.append(current)
                continue

            parts.append(current.prefix + current.opening)
            stack.append(_CLOSING[current.opening])
            last = len(current.items) - 1
            for index in range(last, -1, -1):
                if index != last:
                    stack.append(self.inline_item_sep)
                stack.append(current.items[index])

        return "".join(parts)

    def _indent(self, depth: int) -> str:
        return self.indent_unit * depth

    def _render(self, root: _Container) -> list[str]:
        result: list[str] = []
        stack: list[Any] = [("node", root, 0)]

        while stack:
            action = stack.pop()

            if action[0] == "text":
                result.append(action[1])
                continue
            if action[0] == "suffix":
                result[-1] += action[1]
                continue

            _, node, depth = action
            if not node.items:
                result.append(self._indent(depth) + node.prefix + node.opening + _CLOSING[node.opening])
                continue
            if self._should_collapse(node, depth):
                result.append(self._indent(depth) + self._inline(node))
                continue

            result.append(self._indent(depth) + node.prefix + node.opening)
            stack.append(("text", self._indent(depth) + _CLOSING[node.opening]))

            last = len(node.items) - 1
            for index in range(last, -1, -1):
                item = node.items[index]
                suffix = "" if index == last else self.pretty_item_sep
                if suffix:
                    stack.append(("suffix", suffix))
                if isinstance(item, str):
                    stack.append(("text", self._indent(depth + 1) + item))
                else:
                    stack.append(("node", item, depth + 1))

        return result


def dumps(
    obj: Any,
    *,
    indent: Optional[Union[int, str]] = 4,
    max_depth: Optional[int] = 1,
    compact_leaf: bool = False,
    ensure_ascii: bool = False,
    **json_kwargs: Any,
) -> str:
    """
    Serialize an object to JSON with depth-limited indentation.

    Values, keys, circular references, and custom encoders are handled by the
    standard library through `json.dumps`; this function only reformats the
    resulting text. Arguments such as `skipkeys`, `separators`, `default`,
    `cls`, and `sort_keys` therefore keep their standard-library semantics.

    Args:
        obj: Object to serialize.
        indent: Number of spaces or a custom indentation string, same as
            `json.dumps`. `None` returns compact output unchanged.
        max_depth: Maximum number of container levels to expand. The root
            container counts as level 1. `None` expands every level; values
            below 1 raise an error.
        compact_leaf: When `True`, any list or tuple whose elements are all
            scalars or empty containers stays on one line, taking priority
            over `max_depth`.
        ensure_ascii: When `True`, escape non-ASCII characters. Defaults to
            `False`, unlike `json.dumps`, so non-ASCII text stays readable.
            Pass `True` when the output must be pure ASCII.
        **json_kwargs: Additional arguments forwarded to `json.dumps`. A
            custom `cls` must produce standard JSON text for reformatting.

    Returns:
        The formatted JSON string.

    Raises:
        TypeError: If `max_depth` is not an integer or `None`.
        ValueError: If `max_depth` is below 1, or if `indent` or
            `separators` contain newline characters while reformatting is
            required.

    Examples:
        >>> data = {"a": [1, 2], "b": [3, {"c": 4}]}
        >>> print(dumps(data, indent=2, max_depth=1, compact_leaf=True))
        {
          "a": [1, 2],
          "b": [3, {"c": 4}]
        }
    """
    if max_depth is not None:
        if not isinstance(max_depth, int):
            raise TypeError("max_depth must be an int or None.")
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1 or None.")

    json_kwargs["ensure_ascii"] = ensure_ascii
    text = json.dumps(obj, indent=indent, **json_kwargs)
    if indent is None:
        return text
    # Without a collapsed container, the standard-library output is already final.
    if max_depth is None and not compact_leaf:
        return text

    separators = json_kwargs.get("separators")
    if separators is None:
        item_separator = ","
    else:
        item_separator, key_separator = separators
        if "\n" in item_separator or "\r" in item_separator:
            raise ValueError("separators must not contain newline characters.")
        if "\n" in key_separator or "\r" in key_separator:
            raise ValueError("separators must not contain newline characters.")
    if isinstance(indent, str) and ("\n" in indent or "\r" in indent):
        raise ValueError("indent must not contain newline characters.")

    indent_unit = " " * indent if isinstance(indent, int) else indent
    inline_item_separator = ", " if separators is None else item_separator
    formatter = _Reformatter(
        indent_unit,
        item_separator,
        inline_item_separator,
        max_depth,
        compact_leaf,
    )
    return formatter.reformat(text)


def dump(
    obj: Any,
    fp: TextIO,
    *,
    indent: Optional[Union[int, str]] = 4,
    max_depth: Optional[int] = 1,
    compact_leaf: bool = False,
    ensure_ascii: bool = False,
    **json_kwargs: Any,
) -> None:
    """
    Serialize an object and write it to a text stream.

    Options are the same as `dumps`. Unless `ensure_ascii=True`, the stream
    must accept non-ASCII text; open files with `encoding="utf-8"`.
    """
    fp.write(
        dumps(
            obj,
            indent=indent,
            max_depth=max_depth,
            compact_leaf=compact_leaf,
            ensure_ascii=ensure_ascii,
            **json_kwargs,
        )
    )
