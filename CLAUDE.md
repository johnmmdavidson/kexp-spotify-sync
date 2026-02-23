# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KEXP-Spotify-Sync fetches playlists from any KEXP radio show via the KEXP public API, searches for each track on Spotify, and adds them to a Spotify playlist. It supports browsing all active KEXP programs, selecting specific episodes, and syncing via interactive prompts or CLI arguments. It uses the `spotipy` library for Spotify OAuth and API access.

## Running

```bash
# Activate the virtual environment
source venv/bin/activate

# Interactive mode - browse programs, pick an episode, sync
python main.py

# Direct mode - specify show and date
python main.py --show "Astral Plane" --date 2026-02-19

# Sync to an existing playlist
python main.py --show "Audioasis" --playlist PLAYLIST_ID

# List all active KEXP programs
python main.py --list

# Test KEXP API fetching
python test_kexp.py

# Test Spotify search
python test_spotify.py

# Test Spotify auth
python test_auth.py
```

## Dependencies

Python 3.13 with a local venv. Key packages: `spotipy`, `requests`, `python-dotenv`. Install with:
```bash
pip install -r requirements.txt
```

## Architecture

Four-module design with a single orchestrator:

- **`config.py`** - Spotify credentials (from `.env`) and log file path
- **`kexp_shows.py`** - `KexpShows` class wrapping `/programs/` and `/shows/` endpoints. Lists active programs, fetches episode history with pagination, finds programs by name
- **`kexp_client.py`** - `KexpClient` class that fetches songs from `/plays/?show={id}` for a specific show episode. Paginates results and filters to actual `trackplay` entries
- **`spotify_client.py`** - `SpotifyClient` class wrapping spotipy with OAuth (cache at `.spotify_cache`). Implements a multi-strategy search (exact field search → quoted search → title-only with artist similarity check). Handles playlist creation, track listing, and batch adds (100 per request)
- **`main.py`** - `PlaylistSyncer` orchestrator that wires KEXP fetch → Spotify search → duplicate detection → playlist add, with JSON logging to `sync_log.json`. Supports interactive and direct (CLI) modes via `argparse`

## Key Details

- Spotify credentials are loaded from `.env` via `python-dotenv` (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`).
- Spotify OAuth token is cached in `.spotify_cache` (not committed). First run requires browser-based auth flow via redirect to `127.0.0.1:8080/callback`.
- The KEXP API is unauthenticated and public. Key endpoints: `/programs/`, `/shows/?program={id}`, `/plays/?show={id}`.
- Track fetching uses `/plays/?show={id}` which filters by show instance ID directly — no time-window calculation or timezone conversion needed.
- Playlist naming format: `"{program_name} (KEXP) - {date}"`.
- `sync_log.json` accumulates detailed results of each sync run (found tracks, not-found tracks, duplicates).
- `requirements.txt` pins the direct dependencies.
- `spotify_client.py` uses spotipy's internal `_post`/`_get` methods to call the Feb 2026 Spotify API endpoints directly (`/me/playlists`, `/playlists/{id}/items`) since the built-in spotipy methods still target the old endpoints.
