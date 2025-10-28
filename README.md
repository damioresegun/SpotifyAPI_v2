# SpotyifyAPI_v2

A small and more indepth revamp of the Spotify APIs for making playlists

- Adds this month's liked songs to `Monthly YYYY-MM` (idempotent)
- Archives Discover Weekly into a cumulative archive (idempotent)
- Deletes playlists by regex with `--dry-run` safety

## Quickstart
1. Create a Spotify app: set Redirect URI to `http://127.0.0.1:5000/redirect`
2. Copy `.env.example` -> `.env` and fill in client credentials
3. Install:
   ```bash
   python -m venv .venv && . .venv/bin/activate
   pip install -e .
   # run commands
   spotify-api-v2 monthly
   spotify-api-v2 weekly
   spotify-api-v2 delete "^Monthly \\d{4}-\d{2}$" --dry-run False
    ```
