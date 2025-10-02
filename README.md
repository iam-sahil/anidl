# anidl

anidl is a command-line tool that searches RSS feeds (TokyoTosho, Nyaa.si) for anime, hentai, and JAV torrent releases and helps queue them into aria2 for downloading. It provides a colored, interactive results table, selection prompts, basic history and queue management, and optional magnet metadata enrichment.

This repository is a compact implementation of the core features and is intended to be extended. The main entrypoint is provided as a console script called `anidl`.

Quick start

1. Install (using Poetry):

```powershell
poetry install
poetry run anidl "jujutsu kaisen" --dry-run --verbose
```

2. Typical usage examples:

- Dry-run search (no downloads):

  anidl "jujutsu kaisen" --dry-run

- Search and download (interactive selection):

  anidl "naruto" # prompts for selection then queues to aria2

- Modify config (e.g., change default download directory):

  anidl config --set defaults.download_dir=~/Downloads/anidl

Installed script

- `anidl` -> calls `anidl.cli:cli`

Flags and commands

- `anidl search <query>` : search for query across configured feeds. Important options:

  - `-h/--hentai` : search hentai feeds.
  - `-j/--jav` : search JAV feeds.
  - `-r/--resolution` : append resolution to feed query.
  - `-d/--download-dir` : set download directory (overrides config).
  - `--no-meta` : don't attempt to resolve magnet metadata.
  - `--dry-run` : show results and skip downloads.
  - `--max-connections` : max connections passed to aria2 for new downloads.
  - `--verify/--no-verify` : request aria2 to check integrity when available.
  - `--proxy` : proxy URL (currently accepted by CLI; can be used to wire into fetchers).
  - `--notify/--no-notify` : desktop notifications (plyer) on queueing.
  - `--verbose` : enable verbose/file logging to `~/.anidl/anidl.log`.
  - `--check-update` : (placeholder) check for updates at startup.

- `anidl config [--set key=value] [--user <name>]` : show or modify configuration stored in `~/.anidl/config.toml` or `~/.anidl-<user>/config.toml`. Use `--set` multiple times to apply multiple changes. Supports dot-path keys like `defaults.download_dir`.

- `anidl history` : show previous queued downloads (reads `~/.anidl/history.json`).

- `anidl queue list|pause <gid>|resume <gid>|remove <gid>` : basic aria2 queue control (when aria2 RPC is reachable).

Configuration and files

- Config file: `~/.anidl/config.toml` (created automatically). Defaults include `download_dir`, `resolution`, and `notify`.
- History: `~/.anidl/history.json` stores an append-only list of queued items.
- Logs: `~/.anidl/anidl.log` contains verbose logging if `--verbose` is set.

Developer notes

- Tests: run `pytest -q`. A small test suite is included for parser and CLI integration.
- Code structure: see `docs.md` for an in-depth breakdown of modules and data flow.

Legal / Responsible use
anidl is a tool that interacts with publicly-available RSS feeds and download clients. Users are responsible for ensuring that they have the legal right to download and use any content. Avoid using this tool to obtain copyrighted materials without permission. The author is not responsible for misuse.

Contributing

- Pull requests welcome. Please add tests for new behaviors and keep changes small and focused.

License

- This project scaffold does not include a license file by default. Add one to make your intentions explicit.
