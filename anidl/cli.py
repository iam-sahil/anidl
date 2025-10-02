import asyncio
import json
from pathlib import Path
import click
import logging

from .config import load_config, save_config
# lazy-loaded to avoid importing heavy/optional dependencies (aiohttp) at module import time
# keep module-level names so tests can monkeypatch `cli.fetch_all_feeds`
get_feeds = None
fetch_all_feeds = None
from .parser import parse_feeds
from .utils import parse_selection, ensure_dir, setup_logging
from . import queue as queue_mod
from .utils import load_history, append_history

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


@click.group()
def cli():
    """anidl - search and download anime torrents"""
    pass


@cli.command()
@click.argument("query", nargs=1)
@click.option("-h", "--hentai", is_flag=True, default=False, help="Search hentai feeds (useful when looking for adult-only releases).")
@click.option("-j", "--jav", is_flag=True, default=False, help="Search JAPAN ADULT VIDEO feeds (JAV).")
@click.option("-r", "--resolution", default="-720p -480p -360p", help="Filter resolution (TokyoTosho param). Use negative terms to exclude, e.g. '-720p'.")
@click.option("-d", "--download-dir", default=None, help="Download directory. Defaults to your user Downloads folder if not specified.")
@click.option("--no-meta", is_flag=True, default=False, help="Don't resolve magnet metadata (faster listing, but less precise sizes/titles).")
@click.option("--notify/--no-notify", default=True, help="Enable desktop notifications when downloads complete (uses system notifications).")
@click.option("--dry-run", is_flag=True, default=False, help="Don't actually download, just show results and selections.")
@click.option("--max-connections", default=16, type=int, help="Max connections per download; passed to aria2 when available.")
@click.option("--category", default=None, help="Feed category filter (e.g., sub, raw). Not all feeds support categories.")
@click.option("--proxy", default=None, help="Proxy URL for HTTP(S) requests to fetch RSS feeds (example: http://127.0.0.1:8888)")
@click.option("--lang", default=None, help="Preferred language tag to prefer in results when available.")
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging to the user log file (~/.anidl/anidl.log).")
@click.option("--verify/--no-verify", default=True, help="Request integrity verification from aria2 when supported.")
@click.option("--check-update", is_flag=True, default=False, help="Check PyPI/GitHub for a newer version on startup.")
def search(query, hentai, jav, resolution, download_dir, no_meta, notify, dry_run, max_connections, category, proxy, lang, verbose, verify, check_update):
    """Search for QUERY across configured feeds and optionally download.

    Examples:
      anidl "one piece"                # interactive selection and download
      anidl -h "some query"            # search hentai feeds
      anidl -d "C:\\MyDownloads" "naruto"  # use custom download directory

    Help tips:
    - Use the resolution option to exclude resolutions with a leading '-' (e.g. -r "-720p").
    - Use --dry-run to preview actions without starting downloads.
    """
    # initialize logging
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    config = load_config()
    defaults = config.get("defaults", {})
    # If not provided, default to the user's Downloads folder
    if download_dir is None:
        try:
            downloads = Path.home() / "Downloads"
            download_dir = Path(defaults.get("download_dir", str(downloads)))
        except Exception:
            download_dir = Path(defaults.get("download_dir", "./downloads"))
    else:
        download_dir = Path(download_dir)
    ensure_dir(download_dir)

    mode = "anime"
    if hentai:
        mode = "hentai"
    if jav:
        mode = "jav"

    # lazy import of sources to avoid hard dependency at module import time
    # import each symbol individually only if missing so tests can monkeypatch either one
    global get_feeds, fetch_all_feeds
    try:
        if get_feeds is None:
            from .sources import get_feeds as _gf
            get_feeds = _gf
        if fetch_all_feeds is None:
            from .sources import fetch_all_feeds as _ff
            fetch_all_feeds = _ff
    except Exception:
        click.echo("Missing optional dependency required to fetch feeds (aiohttp).\nPlease install dependencies: `poetry install` or `pip install aiohttp`.")
        return

    feeds = get_feeds(mode, query, resolution)

    async def _run():
        with console.status("Searching..."):
            raw = await fetch_all_feeds(feeds, timeout=10, concurrency=8) if proxy is None else await fetch_all_feeds(feeds, timeout=10, concurrency=8)
        try:
            items = parse_feeds(raw, resolve_magnets=(not no_meta))
        except Exception as e:
            logger.exception("Failed to parse feeds: %s", e)
            click.echo("Error parsing feed results.")
            return

        if not items:
            click.echo("No results found.")
            return

        # Build a rich table for display
        from rich import box
        table = Table(title=f"Search results for: {query}", box=box.MINIMAL)
        table.add_column("#", style="white", width=3)
        table.add_column("Title", style="white")
        table.add_column("Size", style="green", width=12)
        table.add_column("Uploader", style="blue", width=12)
        table.add_column("Date", style="yellow", width=16)
        table.add_column("Health", style="green", width=8)
        table.add_column("Source", style="dim")

        for i, it in enumerate(items, start=1):
            health = float(it.get("health") or 0.0)
            if health > 7:
                health_style = "green"
            elif health > 4:
                health_style = "yellow"
            else:
                health_style = "red"

            table.add_row(
                str(i),
                Text(it.get("title") or "", style="white"),
                Text(it.get("size") or "", style="green"),
                Text(it.get("uploader") or it.get("submitter") or "", style="blue"),
                Text(str(it.get("date")) or "", style="yellow"),
                Text(f"{health:.1f}", style=health_style),
                Text(it.get("source") or "", style="dim"),
            )

        console.print(table)

        if dry_run:
            click.echo("Dry run - skipping downloads.")
            return

        sel = click.prompt("Enter indices (e.g. 1,2,5-7)", default="1")
        indices = parse_selection(sel, len(items))
        selected = [items[i - 1] for i in indices]
        click.echo(f"Selected: {[s.get('title') for s in selected]}")

        # Add to aria2 and show progress (best-effort)
        try:
            from .downloader import add_torrent_or_magnet, download_with_progress
            gids = []
            for s in selected:
                try:
                    gid = add_torrent_or_magnet(
                        s.get("torrent_url") or s.get("magnet") or "",
                        download_dir,
                        pause=False,
                        max_connections=max_connections,
                        verify=verify,
                    )
                    gids.append(gid)
                except Exception as ex:
                    logger.exception("Failed to add to aria2: %s", ex)
                    click.echo(f"Failed to queue {s.get('title')}")

            if gids:
                download_with_progress(gids, download_dir)
                for s in selected:
                    append_history({"title": s.get("title"), "date": str(s.get("date")), "source": s.get("source")})
                if notify:
                    try:
                        from .downloader import notify
                        notify("anidl", f"Downloads queued: {len(gids)}")
                    except Exception:
                        pass
        except Exception as e:
            logger.exception("Download integration failed: %s", e)

    asyncio.run(_run())


@cli.command()
@click.option("--set", "sets", multiple=True, help="Set configuration values (key=value). Can be provided multiple times.")
@click.option("--user", "user", default=None, help="Use a specific user profile for config (separate config dir).")
def config(sets, user):
    """Show or modify config file location and defaults"""
    cfg = load_config(user=user)
    # apply any sets
    if sets:
        for s in sets:
            if "=" not in s:
                click.echo(f"Invalid set value: {s}. Use key=value")
                continue
            k, v = s.split("=", 1)
            # simple dot-path assignment for nested defaults
            parts = k.split(".")
            cur = cfg
            for p in parts[:-1]:
                if p not in cur or not isinstance(cur[p], dict):
                    cur[p] = {}
                cur = cur[p]
            # try to parse common booleans and numbers
            if v.lower() in ("true", "false"):
                val = v.lower() == "true"
            else:
                try:
                    val = int(v)
                except Exception:
                    val = v
            cur[parts[-1]] = val
        save_config(cfg, user=user)
        click.echo("Config updated.")
        return

    click.echo(json.dumps(cfg, indent=2))


@cli.group()
def queue():
    """Manage aria2 queue: list, pause, resume, remove"""
    pass


@queue.command("list")
def queue_list():
    items = queue_mod.list_downloads()
    if not items:
        click.echo("No active downloads.")
        return
    for d in items:
        click.echo(f"{d.get('gid')} - {d.get('name')} - {d.get('status')}")


@queue.command("pause")
@click.argument("gid")
def queue_pause(gid):
    ok = queue_mod.pause(gid)
    click.echo("Paused" if ok else "Failed to pause")


@queue.command("resume")
@click.argument("gid")
def queue_resume(gid):
    ok = queue_mod.resume(gid)
    click.echo("Resumed" if ok else "Failed to resume")


@queue.command("remove")
@click.argument("gid")
def queue_remove(gid):
    ok = queue_mod.remove(gid)
    click.echo("Removed" if ok else "Failed to remove")


@cli.command()
@click.option("--limit", default=50, help="Number of history entries to show")
def history(limit):
    """Show past downloads"""
    items = load_history()
    if not items:
        click.echo("No history.")
        return
    for i, it in enumerate(items[-limit:], start=1):
        click.echo(f"{i}. {it.get('title')} - {it.get('date')}")



if __name__ == "__main__":
    cli()
