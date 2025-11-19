from __future__ import annotations
from .playlists import delete_playlists_by_pattern

def run_delete(sp, user_id: str, pattern: str, dry_run: bool = True):
    matches = delete_playlists_by_pattern(sp, user_id, pattern, dry_run=dry_run)
    return {"matched": len(matches), "playlists": matches, "dry_run": dry_run}
