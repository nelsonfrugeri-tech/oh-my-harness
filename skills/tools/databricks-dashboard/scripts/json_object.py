"""Deeply immutable JSON object values."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Tuple, Union

JsonScalar = Union[None, bool, int, float, str]
JsonValue = Union[JsonScalar, "JsonObject", Tuple["JsonValue", ...]]


@dataclass(frozen=True)
class JsonObject(Mapping[str, JsonValue]):
    """Store a JSON object as recursively frozen key-value pairs."""

    _items: tuple[tuple[str, JsonValue], ...]

    @classmethod
    def from_mapping(cls, value: Mapping[object, object]) -> "JsonObject":
        items: list[tuple[str, JsonValue]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            items.append((key, _freeze(item)))
        return cls(tuple(items))

    def __getitem__(self, key: str) -> JsonValue:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def to_builtin(self) -> dict[str, object]:
        """Return mutable built-ins only at an external serialization boundary."""
        return {key: _thaw(value) for key, value in self._items}


def _freeze(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return JsonObject.from_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _thaw(value: JsonValue) -> object:
    if isinstance(value, JsonObject):
        return value.to_builtin()
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value
