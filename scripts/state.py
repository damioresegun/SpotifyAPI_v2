from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "spotify_api_v2"

@dataclass
class AppState:
    last_monthly_run_utc: str | None = None

    @property
    def last_dt(self):
        if self.last_monthly_run_utc:
            return datetime.fromisoformat(self.last_monthly_run_utc)
        return None
    
def state_path() -> Path:
    d = Path(user_data_dir(APP_NAME))
    d.mkdir(parents=True, exist_ok=True)
    return d / "state.json"

def load_state() -> AppState:
    sp = state_path()
    if sp.exists():
        return AppState(**json.loads(sp.read_text()))
    return AppState()

def save_state(st: AppState) -> None:
    sp = state_path()
    sp.write_text(json.dumps(asdict(st), indent=2))

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

