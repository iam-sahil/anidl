anidl - Developer Documentation

## Overview

This document explains the structure, responsibilities, and internals of the `anidl` project. It is intended for maintainers and contributors who want to extend or harden the tool.

## Top-level layout

- `anidl/` - python package containing the application modules.
- `tests/` - unit and integration tests for core behaviors.
- `pyproject.toml` - package metadata and dependencies.
- `README.md` - user-facing quickstart (see root README).

## Modules and responsibilities

anidl/cli.py

```
- Entrypoint for the CLI via `@click.group()` and subcommands.
- Commands implemented: `search`, `config`, `history`, `queue`.
- `search` flow:
  1. Load configuration via `load_config()` (supports optional `--user` profile).
  2. Build feed URLs using `sources.get_feeds(mode, query, resolution)`.
  3. Fetch feeds concurrently via `sources.fetch_all_feeds` (aiohttp).
  4. Parse feed responses using `parser.parse_feeds(raw_results, resolve_magnets=...)`.
  5. Present results in a `rich.Table`, prompt selection, and optionally queue items with `downloader.add_torrent_or_magnet`.
- Additional behaviors: `--no-meta` to skip magnet enrichment; `--dry-run` skips actual queueing.

anidl/sources.py
```

- Responsible for producing feed URLs and fetching them concurrently.
- `get_feeds(mode, query, resolution)` returns a list of TokyoTosho and nyaa.si RSS URLs depending on mode.
- `fetch_all_feeds(urls, timeout, concurrency)` uses `aiohttp` with a connector and semaphore to fetch feeds concurrently, with retry logic for transient errors.

anidl/parser.py

```
- Parses raw RSS content into normalized item dicts with keys: `title`, `size`, `uploader`, `date` (datetime), `seeders`, `torrent_url`, `source`, `health`.
- Uses regex-based extraction for size and seeders and `difflib.SequenceMatcher` for deduplication.
- `health_score` function computes a combined score based on seeders, age, and uploader trust.
- Optional magnet enrichment: `parse_feeds(..., resolve_magnets=True)` will attempt to call `downloader.resolve_magnet` for magnet URLs to enrich title/size.

anidl/downloader.py
```

- Manages adding torrents/magnets to aria2 via aria2p API or falls back to launching `aria2c` as a subprocess.
- `add_torrent_or_magnet(uri, download_dir, pause=False, max_connections=16, verify=True)` will attempt to pass options such as max connections and integrity checks to aria2.
- `resolve_magnet(uri, timeout)` will add a magnet in paused state and poll aria2 for metadata (requires aria2 RPC and may return None if not available).
- `download_with_progress(gids, download_dir)` uses `rich.Progress` to monitor progress of GIDs via aria2p.
- `notify(title, message)` uses `plyer.notification` to display desktop notifications when available.

anidl/queue.py

```
- Thin wrapper over aria2p to list, pause, resume, and remove downloads.
- Includes a helper to save an aria2 session file under `~/.anidl/aria2.session` when API is available.

anidl/config.py
```

- Reads/writes `~/.anidl/config.toml` (or `~/.anidl-<user>/config.toml` when using per-user profiles).
- `load_config(user=None)` and `save_config(cfg, user=None)` provide a simple persistence layer for defaults and custom feeds.

anidl/utils.py

```
- Utility helpers:
  - `parse_selection` parses user selection strings such as `1,2,5-7` into a sorted list of 1-based indices.
  - `append_history` and `load_history` manage the history file `~/.anidl/history.json`.
  - `setup_logging` configures a rotating/file logger under `~/.anidl/anidl.log` (via FileHandler).

Testing
-------
- Tests under `tests/` include unit tests for parser, utils, and an integration test for CLI dry-run that uses `CliRunner`.
- Run `pytest -q` to execute the test suite.

Extensibility points & TODOs
---------------------------
- Category filtering: Map human-friendly categories to TokyoTosho/Nyaa parameters.
- Proxy wiring: propagate `--proxy` values into `aiohttp` sessions and `requests` usage.
- Rate limiting: implement a token-bucket to avoid exceeding feed providers' request limits.
- Update check: implement `utils.check_version()` to consult a remote manifest and surface updates.
- More robust metadata enrichment: support using libtorrent or trackers for magnet resolution when aria2 RPC isn't available.

Security and privacy notes
--------------------------
- The tool performs network requests; proxies should be used carefully. Credentials should not be stored in config files in plain text.

Support & contribution
----------------------
- Fork and open PRs. Add tests for new behaviors. Keep changes small and document new features in `docs.md`.

Contact
-------
- This codebase is an example scaffold. For questions about the implementation, inspect individual modules in the `anidl` package.
```
