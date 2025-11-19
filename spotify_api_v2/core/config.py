from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    redirect_uri: str
    monthly_prefix: str = ""
    archive_prefix: str = "Discover Weekly Archive"
    monthly_format: str = "month_year" # "month_year" or "yyyy_mm" or "custom:%B %Y"

    @staticmethod
    def from_env() -> "Settings":
        # Fallback values
        default_client_id = "ae971e8139ab4964990a2b08c8549021"
        default_client_secret = "c0f1ae16c37744c5b13368f99aaf1900"
        default_redirect_uri = "http://127.0.0.1:8249/callback"
        cid = os.getenv("SPOTIPY_CLIENT_ID", default_client_id)
        csec = os.getenv("SPOTIPY_CLIENT_SECRET", default_client_secret)
        ruri = os.getenv("SPOTIPY_REDIRECT_URI", default_redirect_uri)
        if not cid or not csec:
            raise RuntimeError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET")
        return Settings(
            client_id=cid,
            client_secret=csec,
            redirect_uri=ruri,
            monthly_prefix=os.getenv("SPOTIFY_MONTH_PREFIX", ""),
            archive_prefix=os.getenv("SPOTIFY_ARCHIVE_PREFIX", "Discover Weekly Archive"),
            monthly_format=os.getenv("SPOTIFY_MONTHLY_FORMAT", "month_year")
        )
