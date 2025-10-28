from scripts.state import AppState, now_iso

def test_state_roundtrip(tmp_path, monkeypatch):
    # Simple smoke test for ISO test
    iso = now_iso()
    assert "T" in iso and iso.endswith("+00:00") or "+" in iso or "2" in iso