# spotify_api_v2/core/playlists.py
from typing import Dict, Any
from spotify_api_v2.core.auth import get_spotify_client, get_current_user_id
from scripts.monthly import run_monthly
from dotenv import load_dotenv
load_dotenv()

MONTHLY_PREFIX = ""
MONTHLY_FORMAT = "month_year"

def create_monthly_playlist() -> Dict[str, Any]:
    """
    Create or update the monthly playlist from liked songs

    This is the function called by the desktop app

    """
    sp = get_spotify_client()
    user_id = get_current_user_id(sp)

    result = run_monthly(
        sp=sp,
        user_id=user_id,
        monthly_prefix=MONTHLY_PREFIX,
        monthly_format=MONTHLY_FORMAT,
    )

    return {
        "ok": True,
        "playlist_name": "Example Monthly Playlist",
        "tracks_added": 0,
        "user_id": user_id,
        **result,
    }