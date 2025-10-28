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
    monthly_prefix: str = "Monthly"
    archive_prefix: str = "Discover Weekly Archive"
    monthly_format: str = "month_year" # "month_year" or "yyyy_mm" or "custom:%B %Y"

    @staticmethod
    def from_env() -> "Settings":
        cid = os.getenv("SPOTIPY_CLIENT_ID")
        csec = os.getenv("SPOTIPY_CLIENT_SECRET")
        ruri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/redirect")
        if not cid or not csec:
            raise RuntimeError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET")
        return Settings(
            client_id=cid,
            client_secret=csec,
            redirect_uri=ruri,
            monthly_prefix=os.getenv("SPOTIFY_MONTH_PREFIX", "Monthly"),
            archive_prefix=os.getenv("SPOTIFY_ARCHIVE_PREFIX", "Discover Weekly Archive"),
            monthly_format=os.getenv("SPOTIFY_MONTHLY_FORMAT", "month_year")
        )
