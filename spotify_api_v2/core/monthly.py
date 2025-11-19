from __future__ import annotations
import logging
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import time
import requests
from spotify_api_v2.core.playlists import month_key, ensure_playlist, add_tracks_dedup, format_month

logger = logging.getLogger(__name__)

def _parse_yyyymm(s: str) -> datetime:
    # s like "2024-01" -> first day of that month UTC
    return datetime.fromisoformat(f"{s}-01T00:00:00+00:00")


def run_monthly(sp, user_id: str, monthly_prefix: str, monthly_format: str) -> dict:
    start_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    #mk = month_key()
    #playlist_name = f"{monthly_prefix} {mk}"
    playlist_name = format_month(start_month, monthly_prefix, monthly_format)
    pid = ensure_playlist(sp, user_id, playlist_name, public=False)

    # Fetch liked songs (saved tracks) since start of the month, then dedupe add
    # Note: Spotify saved tracks are reverse chronological, thus filter by added_at >= first day of the month UTC
    start_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    to_add = []
    for it in iter_saved_tracks(sp, limit=50):
        added_at = it.get("added_at")
        track = it.get("track") or {}
        uri = track.get("uri")
        if not uri or not added_at:
            continue
        try:
            added_dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if added_dt >= start_month:
            to_add.append(uri)
        else:
            # since list is reverse chronological, once we pass threshold we can stop early
            break
    
    added = add_tracks_dedup(sp, pid, to_add)
    return {"playlist_id": pid, "playlist_name": playlist_name, "added": added}


def iter_saved_tracks(sp, limit: int=50, max_retries: int=3):
    """
    Generator over all saved tracks, with basic retry on connection errors
    """
    offset = 0
    while True:
        for attempt in range(max_retries):
            try:
                res = sp.current_user_saved_tracks(limit=limit, offset=offset)
                break
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1.0)
        items = res.get("items", [])
        if not items:
            break
        yield from items
        if not res.get("next"):
            break
        offset += limit


def run_monthly_backfill(
        sp,
        user_id: str,
        monthly_prefix: str,
        monthly_format: str,
        since_yyyymm: str | None = None,
        months: int | None = None,
        until_yyyymm: str | None = None,
) -> dict:
    """Build monthly playlist for past months by grouping several saved tracks by their added_at
    month. Idempotent readout. You can specify either since_yyyymm e.g. 2024-01 or months=6
    """
    now = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if since_yyyymm:
        start = _parse_yyyymm(since_yyyymm)
    elif months:
        start = (now - relativedelta(months=months)).replace(day=1)
    else:
        raise ValueError("Provide since_yyyymm='YYYY-MM' or months=N")
    
    end = _parse_yyyymm(until_yyyymm) if until_yyyymm else now

    # Build month buckets (ordered chronologically)
    buckets: "OrderedDict[str, list[str]]" = OrderedDict()

    limit, offset = 50, 0
    while True:
        res = fetch_saved_tracks_page(sp, limit=limit, offset=offset)
        items = res.get("items", [])
        if not items:
            break
        all_older_than_start = True
        for it in items:
            added_at = it.get("added_at")
            track = (it.get("track") or {})
            uri = track.get("uri")
            if not uri or not added_at:
                continue
            added_dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
            if added_dt < start:
                # below lower bound; keep scanning older pages just in case there are sparse entries
                continue
            if added_dt >= end + relativedelta(months=1):
                # newer than upper bound; still count toward buckets but no need to stop
                pass
            # month key for this track
            mk = added_dt.strftime("%Y-%m")
            buckets.setdefault(mk, []).append(uri)
            if added_dt >= start:
                all_older_than_start = False

        if res.get("next"):
            offset += limit
            # optimization: if entire page was older than start AND results are sorted desc,
            # we could break early; Spotipy returns reverse-chronological, so we can stop.
            if all_older_than_start:
                break
        else:
            break

    # Now create/append for each bucket within [start, end]
    results = []
    current = start
    while current <= end:
        mk = current.strftime("%Y-%m")
        uris = buckets.get(mk, [])
        playlist_name = format_month(current, monthly_prefix, monthly_format)
        pid = ensure_playlist(sp, user_id, playlist_name, public=False)
        added = add_tracks_dedup(sp, pid, uris)
        results.append({"month": mk, "playlist_name": playlist_name, "added": added})
        current += relativedelta(months=1)

    return {"created_or_updated": results}


def fetch_saved_tracks_page(sp, limit:int, offset: int, max_retries: int = 3, base_delay: float = 1.0):
    """
    Fetch a single page of saved tracks with basic retry and backoff

    Retries on ConnectionError and ReadTimeout from requests/urllib3
    """
    for attempt in range(max_retries):
        try:
            return sp.current_user_saved_tracks(limit=limit, offset=offset)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            # Last attempt: re-raise
            if attempt == max_retries - 1:
                raise
            # Backoff a bit and try again
            delay = base_delay * (attempt + 1)
            print(f"[monthly backfill] transient error: {e} (attempt {attempt+1}/{max_retries}), retrying in {delay:.1f}s")
            time.sleep(delay)
