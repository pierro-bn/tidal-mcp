"""Compact read responses. Mutation previews never pass through this module."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Literal, get_type_hints

from pydantic import BaseModel

Detail = Literal["compact", "detailed"]
SECONDARY = {"url", "description", "creator", "created_at", "updated_at", "artist_id", "album_id"}


def compact(value: Any) -> Any:
    if isinstance(value, list):
        return [compact(item) for item in value]
    if isinstance(value, dict):
        return {key: compact(item) for key, item in value.items() if key not in SECONDARY}
    return value


def compact_output(function: Any) -> Any:
    """Add a validated detail argument while keeping original inputs intact."""
    signature = inspect.signature(function)
    hints = get_type_hints(function, include_extras=True)
    parameters = [
        p.replace(annotation=hints.get(p.name, p.annotation)) for p in signature.parameters.values()
    ]
    parameters.append(
        inspect.Parameter(
            "detail", inspect.Parameter.KEYWORD_ONLY, default="compact", annotation=Detail
        )
    )

    @functools.wraps(function)
    async def wrapper(*args: Any, detail: Detail = "compact", **kwargs: Any) -> dict[str, Any]:
        value = await function(*args, **kwargs)
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        return compact(value) if detail == "compact" else value

    wrapper.__signature__ = signature.replace(
        parameters=parameters, return_annotation=dict[str, Any]
    )
    wrapper.__annotations__ = {p.name: p.annotation for p in parameters}
    wrapper.__annotations__["return"] = dict[str, Any]
    return wrapper


def check_favorites(client: Any, track_ids: list[str], max_pages: int) -> dict[str, Any]:
    """Scan privately; only return candidate membership, with explicit coverage."""
    ids = list(dict.fromkeys(track_ids))
    found: set[str] = set()
    offset = 0
    complete = False
    reason = "scan_limit"
    for _ in range(max_pages):
        try:
            page = client.list_favorite_tracks(50, offset)
        except Exception:
            reason = "read_failed"
            break
        found.update(track.id for track in page.items if track.id in ids)
        if not page.has_more:
            complete = True
            reason = "complete"
            break
        if len(found) == len(ids):
            reason = "all_candidates_found"
            break
        if page.next_offset is None or page.next_offset <= offset:
            reason = "invalid_pagination"
            break
        offset = page.next_offset
    return {
        "complete": complete,
        "reason": reason,
        "items": [
            {
                "id": track_id,
                "status": "favorite"
                if track_id in found
                else "not_favorite"
                if complete
                else "unknown",
            }
            for track_id in ids
        ],
    }
