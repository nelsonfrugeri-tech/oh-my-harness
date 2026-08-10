"""Validate immutable Lakeview page and layout structures."""

from __future__ import annotations

from dashboard_models import Definition
from json_object import JsonObject, JsonValue


def definition_errors(definition: Definition) -> tuple[str, ...]:
    """Return structural errors in a dashboard definition."""
    pages = definition.serialized_dashboard.get("pages")
    if not isinstance(pages, tuple) or not pages:
        return ("serialized_dashboard.pages must be a non-empty list",)
    names = tuple(dataset.name for dataset in definition.datasets)
    duplicate_error = (
        ("dataset names must be unique",) if len(names) != len(set(names)) else ()
    )
    return duplicate_error + tuple(
        error for index, page in enumerate(pages) for error in _page_errors(page, index)
    )


def _page_errors(value: JsonValue, index: int) -> tuple[str, ...]:
    if not isinstance(value, JsonObject):
        return (f"page {index} must be an object",)
    layout = value.get("layout")
    if not isinstance(layout, tuple) or not layout:
        return (f"page {index} layout must be a non-empty list",)
    return tuple(
        error
        for widget_index, item in enumerate(layout)
        for error in _layout_errors(item, index, widget_index)
    )


def _layout_errors(item: JsonValue, page: int, widget: int) -> tuple[str, ...]:
    if not isinstance(item, JsonObject):
        return (f"page {page} layout {widget} must contain a widget object",)
    widget_error = (
        ()
        if isinstance(item.get("widget"), JsonObject)
        else (f"page {page} layout {widget} must contain a widget object",)
    )
    position_error = (
        ()
        if _valid_position(item.get("position"))
        else (f"page {page} layout {widget} has an invalid position",)
    )
    return widget_error + position_error


def _valid_position(value: JsonValue) -> bool:
    if not isinstance(value, JsonObject):
        return False
    keys = ("x", "y", "width", "height")
    return all(_is_non_negative_integer(value.get(key)) for key in keys)


def _is_non_negative_integer(value: JsonValue) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
