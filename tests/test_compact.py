import asyncio
from types import SimpleNamespace

from tidal_mcp.output import check_favorites, compact
from tests.test_server import make_runtime, call


def test_compact_preserves_matching_and_pagination():
    value = {
        "items": [
            {
                "id": "1",
                "title": "Track",
                "artist": "Artist",
                "url": "long",
                "allowStreaming": False,
            }
        ],
        "has_more": True,
        "next_offset": 50,
    }
    assert compact(value) == {
        "items": [{"id": "1", "title": "Track", "artist": "Artist", "allowStreaming": False}],
        "has_more": True,
        "next_offset": 50,
    }
    assert value["items"][0]["url"] == "long"


def test_favorites_pagination_and_failed_reads():
    class Music:
        def list_favorite_tracks(self, limit, offset):
            if offset == 0:
                return SimpleNamespace(
                    items=[SimpleNamespace(id="1")], has_more=True, next_offset=50
                )
            return SimpleNamespace(
                items=[SimpleNamespace(id="2")], has_more=False, next_offset=None
            )

    assert [i["status"] for i in check_favorites(Music(), ["1", "2", "3"], 2)["items"]] == [
        "favorite",
        "favorite",
        "not_favorite",
    ]
    assert check_favorites(Music(), ["2"], 1)["items"][0]["status"] == "unknown"

    class Broken(Music):
        def list_favorite_tracks(self, limit, offset):
            if offset:
                raise RuntimeError("private details must not leak")
            return super().list_favorite_tracks(limit, offset)

    result = check_favorites(Broken(), ["1", "2"], 2)
    assert [i["status"] for i in result["items"]] == ["favorite", "unknown"]
    assert result["reason"] == "read_failed"


def test_mcp_compact_and_detailed(tmp_path):
    runtime, _ = make_runtime(tmp_path)
    small = asyncio.run(call(runtime, "tidal_list_favorite_tracks", {"detail": "compact"}))
    full = asyncio.run(call(runtime, "tidal_list_favorite_tracks", {"detail": "detailed"}))
    assert small == compact(full)
    assert "url" in full["items"][0]
    assert "url" not in small["items"][0]
