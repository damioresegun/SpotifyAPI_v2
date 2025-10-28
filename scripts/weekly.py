from __future__ import annotations
import logging
from .playlists import ensure_playlist, add_track_dedup, get_playlist_tracks

logger = logging.getLogger(__name__)

DISCOVER_WEEKLY_ID = "37i9dQZEVXcJZyENR7Zx2C" # placeholder text

def run_discover_weekly_archive(sp, user_id: str, archive_prefix: str = "Discover Weekly Archive") -> dict:
    # Find Discover Weekly by name under current user (not guaranteed to be stable ID)
    dw_id = None
    limit, offset = 50, 0
    while True:
        res = sp.current_user_playlists(limit=limit, offset=offset)
        for pl in res.get("items", []):
            if pl.get("name", "").lower() == "discover weekly":
                dw_id = pl.get("id")
                break
        if dw_id or not res.get("next"):
            break
        offset += limit
    
    if not dw_id:
        return {"archived": 0, "reason": "Discover Weekly not found"}
    
    archive_id = ensure_playlist(sp, user_id, archive_prefix, public=False)
    uris = get_playlist_tracks(sp, dw_id)
    added = add_track_dedup(sp, archive_id, uris)
    return {"playlist_id": archive_id, "archived": added}