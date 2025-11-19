# spotify_api_v2/desktop/app_fastapi.py

from pathlib import Path
import webbrowser
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv
from spotify_api_v2.core.cli import get_client
from spotify_api_v2.core.monthly import run_monthly, run_monthly_backfill
import requests
from typing import Optional
from pydantic import BaseModel
import threading
import time
import os


# Load env vars from .env
load_dotenv()

app = FastAPI(title="SpotifyAPI_v2 Desktop")

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

class BackfillRequest(BaseModel):
    months: Optional[int] = None
    from_start: bool = False

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = UI_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>UI not found</h1><p>Expected spotify_api_v2/desktop/ui/index.html</p>",
            status_code=500,
        )
    return index_path.read_text(encoding="utf-8")


@app.get("/api/status")
def api_status():
    return {
        "status": "ok",
        "message": "Backend is running and ready to talk to Spotify.",
    }


@app.post("/api/login")
def api_login():
    print(">>> /api/login handler reached")
    try:
        sp, user_id, settings = get_client()
        me = sp.current_user()
        display_name = me.get("display_name") or user_id
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "ok": True,
        "user_id": user_id,
        "display_name": display_name,
    }


@app.post("/api/playlists/monthly")
def api_create_monthly():
    print(">>> /api/playlists/monthly handler reached")
    try:
        sp, user_id, settings = get_client()
        res = run_monthly(
            sp=sp,
            user_id=user_id,
            monthly_prefix=settings.monthly_prefix,
            monthly_format=settings.monthly_format,
        )
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Spotify API connection error: {e}",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "ok": True,
        **res,
    }


@app.post("/api/playlists/monthly/backfill")
def api_backfill_monthly(payload: BackfillRequest):
    """
    Backfil monthly playlists for the last N months
    
    If from_start is True: backfill from 'start of account'
    Otherwise backfill the last 'months_variable' months (default is 3)
    """
    print(">>> /api/playlists/monthly/backfill handler reached")
    try:
        sp, user_id, settings = get_client()

        if payload.from_start:
            since_yyyymm = "2008-10"    #TODO: expose start from year and month to user. Not just months
            months = None
        else:
            months = payload.months or 3
            if months <= 0: # TODO: does this mean the current month wont be generated?
                raise HTTPException(status_code=400, detail="months must be a positive integer")
            since_yyyymm = None

        res = run_monthly_backfill(
            sp=sp,
            user_id=user_id,
            monthly_prefix=settings.monthly_prefix,
            monthly_format=settings.monthly_format,
            since_yyyymm=since_yyyymm,
            months=months,
        )
    except requests.exceptions.ConnectionError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Spotify API connection error during backfill: {e}",
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "ok": True,
        "from_start": payload.from_start,
        "months_requested": payload.months,
        **res,
    }

@app.post("/api/shutdown")
def shutdown():
    """
    Gracefully shutdown the FastAPI/Uvicorn server and exit the app
    """
    print(">>> Shutdown requested from frontend")

    # Return response FIRST
    def delayed_exit():
        time.sleep(0.5)
        print(">>> Shutdown requested from frontend")
        os._exit(0)
    
    threading.Thread(target=delayed_exit).start()

    return {
        "ok": True,
        "message": "Shutting down...",
    }

def run():
    port = 8249
    url = f"http://127.0.0.1:{port}"
    print(f"Starting desktop app at {url}")
    webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    run()
