import os
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Scopes needed for your monthly logic
SCOPES = [
    "user-library-read",
    "playlist-modify-public",
    "playlist-modify-private",
    "playlist-read-private",
]
SCOPE_STR = " ".join(SCOPES)


def get_auth_manager() -> SpotifyOAuth:
    """
    Return a SpotifyOAuth manager that ONLY uses a cached token.
    It will NOT run the interactive flow from inside FastAPI.
    """
    # Support both SPOTIFY_* and SPOTIPY_* env names
    client_id = os.environ.get("SPOTIFY_CLIENT_ID") or os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET") or os.environ.get("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI") or os.environ.get("SPOTIPY_REDIRECT_URI")

    if not client_id:
        raise RuntimeError("SPOTIFY_CLIENT_ID or SPOTIPY_CLIENT_ID not set in environment")
    if not client_secret:
        raise RuntimeError("SPOTIFY_CLIENT_SECRET or SPOTIPY_CLIENT_SECRET not set in environment")
    if not redirect_uri:
        raise RuntimeError("SPOTIFY_REDIRECT_URI or SPOTIPY_REDIRECT_URI not set in environment")

    # IMPORTANT: no cache_path here -> Spotipy uses the default '.cache' in CWD
    # and we set open_browser=False so it never tries to launch interactive auth.
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE_STR,
        open_browser=False,
    )


def get_spotify_client() -> spotipy.Spotify:
    """
    Create a Spotify client using ONLY a cached token.

    If no cached token exists, we raise an error and tell the user
    to run the CLI auth first.
    """
    auth_manager = get_auth_manager()
    token_info = auth_manager.get_cached_token()

    if not token_info:
        raise RuntimeError(
            "No cached Spotify token found.\n"
            "Run your existing CLI script once (the one that already works) "
            "to log in and create the .cache file, then try again."
        )

    access_token = token_info["access_token"]
    return spotipy.Spotify(auth=access_token)


def get_current_user_id(sp: Optional[spotipy.Spotify] = None) -> str:
    if sp is None:
        sp = get_spotify_client()
    me = sp.me()
    return me["id"]
