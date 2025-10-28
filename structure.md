spotify_api_v2/
|-- pyproject.toml
|-- README.md
|-- .gitignore
|-- .env.example
|-- scripts/
|   |-- __init__.py
|   |-- config.py       # env & settings validation
|   |-- auth.py         # OAuth (Spotify wrapper) & cache pathing
|   |-- client.py       # Spotify client factory + retry session
|   |-- state.py        # last-run timestamps, cached IDs
|   |-- playlists.py    # reusable playlist helpers
|   |-- monthly.py      # "liked -> Monthly YYYY-MM" logic
|   |-- weekly.py       # Discover Weekly archive logic
|   |-- delete.py       # Batch delete with --dry-run/--force
|   |-- cli.py          # Typer entry points
|-- tests/
|   |-- test_naming.py
|   |-- test_state.py
|   |-- test_idempotency.py
