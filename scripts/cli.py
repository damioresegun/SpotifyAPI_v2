from __future__ import annotations
import logging
import typer
from spotipy import Spotify
from .config import Settings
from .auth import build_oauth
from .client import make_client
from .monthly import run_monthly, run_monthly_backfill
from .weekly import run_discover_weekly_archive
from .delete import run_delete

app = typer.Typer(add_completion=False)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

def get_client() -> tuple[Spotify, str, Settings]:
    settings = Settings.from_env()
    scope = "user-library-read playlist-modify-public playlist-modify-private playlist-read-private"
    oauth = build_oauth(settings, scope)
    sp = make_client(oauth)
    me = sp.current_user()
    return sp, me["id"], settings

@app.command()
def monthly():
    """Add liked songs fro the current month to the `Monthly YYYY-MM` playlist (idempotent)."""
    sp, user_id, settings = get_client()
    res = run_monthly(sp, user_id, monthly_prefix=settings.monthly_prefix, monthly_format=settings.monthly_format)
    typer.echo(res)

@app.command()
def weekly():
    """Archive Discover Weekly tracks into a cumulative archive playlist"""
    sp, user_id, settings = get_client()
    res = run_discover_weekly_archive(sp, user_id, archive_prefix=settings.archive_prefix)
    typer.echo(res)

@app.command()
def delete(
    pattern: str = typer.Option(r"^(Monthly|Discover Weekly Archive).*", "--pattern", "-p"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
):
    """Delete playlists whose names match a regex. Defaults to dry-run; pass --dry-run False to execute"""
    sp, user_id, _ = get_client()
    res = run_delete(sp, user_id, pattern=pattern, dry_run=dry_run)
    typer.echo(res)


@app.command()
def backfill(
    since: str = typer.Option(None, "--since", help="YYYY-MM lower bound, e.g. 2024-01"),
    months: int = typer.Option(None, "--months", help="Backfill the last N months"),
    until: str = typer.Option(None, "--until", help="YYYY-MM upper bound (inclusive). Defaults to current month."),
):
    """Retroactively create/update Monthly playlists from Saved Tracks history."""
    sp, user_id, settings = get_client()
    res = run_monthly_backfill(
        sp, user_id,
        monthly_prefix=settings.monthly_prefix,
        monthly_format=settings.monthly_format,
        since_yyyymm=since,
        months=months,
        until_yyyymm=until,
    )
    typer.echo(res)

if __name__ == "__main__":
    app()