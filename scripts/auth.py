from __future__ import annotations
from pathlib import Path
from platformdirs import user_cache_dir
from spotipy.oauth2 import SpotifyOAuth
from .config import Settings

APP_NAME = "spotify_api_v2"

def token_cache_path() -> str:
    cache_dir = Path(user_cache_dir(APP_NAME))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / ".cache")

def build_oauth(settings: Settings, scope: str) -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        redirect_uri=settings.redirect_uri,
        scope=scope,
        cache_path=token_cache_path(),
        open_browser=True,
        requests_timeout=30,
    )
