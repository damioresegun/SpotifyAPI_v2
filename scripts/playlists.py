from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Iterable
from .client import retryable
import calendar

logger = logging.getLogger(__name__)

def month_key(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m")


def format_month(dt: datetime, monthly_prefix: str, monthly_format: str) -> str:
    """Return playlist name per format setting."""
    if monthly_format == "month_year":
        name = f"{calendar.month_name[dt.month]} {dt.year}"  # e.g., September 2025
    elif monthly_format == "yyyy_mm":
        name = dt.strftime("%Y-%m")  # FIX: %Y, not $Y
    elif monthly_format.startswith("custom"):
        fmt = monthly_format.split("custom:", 1)[1] if ":" in monthly_format else "%B %Y"
        name = dt.strftime(fmt)
    else:
        name = f"{calendar.month_name[dt.month]} {dt.year}"

    # Only include the prefix if it’s non-empty (after strip).
    prefix = (monthly_prefix or "").strip()
    final = " ".join(part for part in [prefix, name] if part)
    return final


def current_month_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@retryable
def ensure_playlist(sp, user_id: str, name: str, public: bool = False) -> str:
    # find existing by name (first match)
    limit, offset = 50, 0
    while True:
        res = sp.current_user_playlists(limit=limit, offset=offset)
        for pl in res.get("items", []):
            if pl.get("name") == name and pl.get("owner", {}).get("id") == user_id:
                return pl["id"]
        if res.get("next"):
            offset += limit
        else:
            break
    created = sp.user_playlist_create(user_id, name, public=public)
    return created["id"]

@retryable
def get_playlist_tracks(sp, playlist_id: str) -> list[str]:
    uris: list[str] = []
    limit, offset = 100, 0
    while True:
        res = sp.playlist_items(
            playlist_id, fields="items(track(uri)),next", limit=limit, offset=offset
        )
        for it in res.get("items", []):
            t = it.get("track")
            if t and t.get("uri"):
                uris.append(t["uri"])
        if res.get("next"):
            offset += limit
        else:
            break
    return uris

@retryable
def add_tracks_dedup(sp, playlist_id: str, new_uris: Iterable[str]) -> int:
    existing = set(get_playlist_tracks(sp, playlist_id))
    to_add = [u for u in new_uris if u not in existing]
    if not to_add:
        return 0
    # add in chunks of 100
    for i in range(0, len(to_add), 100):
        sp.playlist_add_items(playlist_id, to_add[i : i + 100])
    return len(to_add)

@retryable
def delete_playlists_by_pattern(sp, user_id: str, pattern, dry_run: bool = True) -> list[tuple[str, str]]:
    """
    Return list of (id, name) that match; delete if not dry-run.
    """
    import re
    matches: list[tuple[str, str]] = []
    limit, offset = 50, 0
    while True:
        res = sp.current_user_playlists(limit=limit, offset=offset)
        for pl in res.get("items", []):
            name = pl.get("name", "")
            if re.search(pattern, name):
                matches.append((pl["id"], name))
        if res.get("next"):
            offset += limit
        else:
            break

    if not dry_run:
        for pid, _ in matches:
            sp.current_user_unfollow_playlist(pid)

    return matches