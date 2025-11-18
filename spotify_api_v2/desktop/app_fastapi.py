import webbrowser
from fastapi import FastAPI
import uvicorn
from pathlib import Path
from fastapi.responses import HTMLResponse
from spotify_api_v2.core.playlists import create_monthly_playlist
from spotify_api_v2.core.auth import get_spotify_client, get_current_user_id
from spotify_api_v2.core.playlists import create_monthly_playlist
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SpotifyAPI_v2 Desktop")

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

@app.get("/", response_class=HTMLResponse)
def serve_index():
    """
    Serve the static index.html as the main UI
    """
    index_path = UI_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>UI not found</h1><p>Expected desktop/ui/index.html</p>",
            status_code=500,
        )
    return index_path.read_text(encoding="utf-8")

@app.get("/api/status")
def api_status():
    """
    Simple JSON endpoint so the frontend can check the backend
    """
    return {
        "status": "ok",
        "message": "Backend is running and ready to be wired to Spotify",
    }


@app.post("/api/playlists/monthly")
def api_create_monthly():
    """
    Trigger creation of the monthly playlist

    For now this just calls a stub function; later it will call your real Spotify logic
    """
    result = create_monthly_playlist()
    return result


@app.post("/api/login")
def api_login():
    """
    Trigger Spotify login/consent via Spotipy

    On first run, this will open the browser to Spotify; on later runs, 
    this will reuse the cached token
    """
    sp = get_spotify_client()
    user_id = get_current_user_id(sp)
    me = sp.me()
    display_name = me.get("display_name") or user_id

    return {
        "ok": True,
        "user_id": user_id,
        "display_name": display_name,
    }

# @app.get("/")
# def read_root():
#     # placeholder to hold buttons
#     return {"status": "ok", "message": "Desktop shell is running"}


def run():
    # TODO: Change the port later
    port = 8249
    url = f"http://127.0.0.1:{port}"
    print(f"Starting desktop app at {url}")
    webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    run()
