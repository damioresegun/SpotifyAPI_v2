from __future__ import annotations
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

def make_client(oauth: SpotifyOAuth) -> Spotify:
    # spotipy already refreshes token, but wrap calls with retry via helpers below
    return Spotify(auth_manager=oauth)

def retryable(fn):
    # Add retry behaviour to small client callables
    return retry(
        wait=wait_exponential(min=1, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )(fn)