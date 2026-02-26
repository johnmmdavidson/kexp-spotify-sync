# KEXP Spotify Sync

Turn any [KEXP](https://kexp.org) radio show into a Spotify playlist. Browse programs, pick an episode, and sync the tracklist — or automate it with CLI flags.

## What it does

1. Fetches the tracklist from a KEXP show episode via the public KEXP API
2. Searches for each track on Spotify using a multi-strategy search (exact match, quoted search, fuzzy artist matching)
3. Creates a Spotify playlist and adds the found tracks, skipping duplicates

## Setup

### Prerequisites

- Python 3.13+
- A [Spotify Developer](https://developer.spotify.com/dashboard) application

### Install

```bash
git clone https://github.com/YOUR_USERNAME/kexp-spotify-sync.git
cd kexp-spotify-sync
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Spotify credentials

```bash
cp .env.example .env
```

Edit `.env` with your Spotify app credentials:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080/callback
```

Your Spotify app must have `http://127.0.0.1:8080/callback` as a redirect URI in its settings.

On first run, a browser window will open for Spotify OAuth. The token is cached locally in `.spotify_cache` for subsequent runs.

## Usage

### Interactive mode

Browse all active KEXP programs, pick an episode, and sync:

```bash
python main.py
```

### Direct mode

Sync a specific show and date:

```bash
python main.py --show "Astral Plane" --date 2026-02-19
```

Sync the latest episode of a show:

```bash
python main.py --show "Audioasis" --latest
```

Sync into an existing playlist instead of creating a new one:

```bash
python main.py --show "Audioasis" --latest --playlist PLAYLIST_ID
```

### Other options

```bash
# List all active KEXP programs
python main.py --list

# Preview what would sync without touching Spotify
python main.py --show "Midnight in a Perfect World" --latest --dry-run
```

## How search works

Spotify search uses three strategies in order:

1. **Exact field search** — `track:"Song Name" artist:"Artist Name" album:"Album"`
2. **Quoted search** — `"Artist Name" "Song Name"` as a combined query
3. **Title-only with artist similarity** — searches by song title, then filters results by how closely the artist name matches

This catches most tracks, including ones with slight naming differences between KEXP metadata and Spotify's catalog.

## Project structure

```
main.py            # CLI entrypoint and orchestrator
config.py          # Loads Spotify credentials from .env
kexp_client.py     # Fetches songs from a KEXP show episode
kexp_shows.py      # Lists KEXP programs and episodes
spotify_client.py  # Spotify OAuth, search, and playlist management
```

## License

[MIT](LICENSE)
