# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KEXP-Spotify-Sync fetches the playlist from a specific weekly KEXP radio show (Wednesday 7-10 PM Pacific) via the KEXP public API, searches for each track on Spotify, and adds them to a Spotify playlist. It uses the `spotipy` library for Spotify OAuth and API access.

## Running

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the main sync
python main.py

# Test KEXP API fetching
python test_kexp.py

# Test Spotify search
python test_spotify.py

# Test Spotify auth
python test_auth.py
```

## Dependencies

Python 3.13 with a local venv. Key packages: `spotipy`, `requests`, `pytz`, `python-dotenv`. Install with:
```bash
pip install -r requirements.txt
```

## Architecture

Three-module design with a single orchestrator:

- **`config.py`** - Spotify credentials, show schedule constants (day, hours, playlist location), log file path
- **`kexp_client.py`** - `KexpClient` class that fetches songs from `api.kexp.org/v2/plays/` for a given date's show window, converts Pacific time to UTC, paginates results, and filters to actual `trackplay` entries
- **`spotify_client.py`** - `SpotifyClient` class wrapping spotipy with OAuth (cache at `.spotify_cache`). Implements a multi-strategy search (exact field search → quoted search → title-only with artist similarity check). Handles playlist creation, track listing, and batch adds (100 per request)
- **`main.py`** - `PlaylistSyncer` orchestrator that wires KEXP fetch → Spotify search → duplicate detection → playlist add, with JSON logging to `sync_log.json`

## Key Details

- Spotify credentials are loaded from `.env` via `python-dotenv` (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`).
- Spotify OAuth token is cached in `.spotify_cache` (not committed). First run requires browser-based auth flow via redirect to `127.0.0.1:8080/callback`.
- The KEXP API is unauthenticated and public. Pagination uses offset/limit params with `airdate_after` ordering.
- Show time window is configured in `config.py` and defaults to Wednesday 7-10 PM Pacific (playlist location 3).
- `sync_log.json` accumulates detailed results of each sync run (found tracks, not-found tracks, duplicates).
- `requirements.txt` pins the four direct dependencies.
- `spotify_client.py` uses spotipy's internal `_post`/`_get` methods to call the Feb 2026 Spotify API endpoints directly (`/me/playlists`, `/playlists/{id}/items`) since the built-in spotipy methods still target the old endpoints.
