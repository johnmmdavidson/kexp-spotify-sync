import os
from dotenv import load_dotenv

load_dotenv()


# Spotify API credentials (loaded from .env)
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")

# Show configuration
SHOW_NAME = "Astral Plane"
SHOW_DAY = 2  # Wednesday (0=Monday, 1=Tuesday, 2=Wednesday...)
SHOW_START_HOUR = 19  # 7 PM
SHOW_END_HOUR = 22    # 10 PM (exclusive, so 9:59 PM)
KEXP_PLAYLIST_LOCATION = 3  # From the API URL

# Logging
LOG_FILE = "sync_log.json"
