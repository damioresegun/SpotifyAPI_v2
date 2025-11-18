import os
from pathlib import Path
from typing import Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPES = [
    "user-library-read",
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
]

SCOPE_STR = " ".join(SCOPES)

def get_cache_path() -> str:
    """
    Where Spotipy will store token information (per user, per machine)
    This is all local so nothing is sent to a server (there is no server)
    """
    base = Path.home() / ".spotify_api_v2"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / "token_cache.json")


def get_auth_manager() -> SpotifyOAuth:
    """
    Return a SpotifyOAuth auth manager
    This will:
    - open the browser (maybe) for login/consent on first run
    - store tokens in a local cache file
    - refresh tokens automatically when they expire
    """
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

    if not client_id:
        raise RuntimeError("SPOTIFY_CLIENT_ID not set in the environment")
    if not redirect_uri:
        raise RuntimeError("SPOTIFY_REDIRECT_URI not set in the environment")
    
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE_STR,
        cache_path=get_cache_path(),
        open_browser=True,
    )


def get_spotify_client() -> spotipy.Spotify:
    """
    Return an authenticated Spotify client.
    - On first call, this will trigger the browser login/consent flow
    - On subsequent calls, it uses the cached token (and refreshes as needed)
    """
    auth_manager = get_auth_manager()
    return spotipy.Spotify(auth_manager=auth_manager)


def get_current_user_id(sp: Optional[spotipy.Spotify] = None) -> str:
    """
    Convenience helper to get the current Spotify User ID
    """
    if sp is None:
        sp = get_spotify_client()
    me = sp.me()
    return me["id"]