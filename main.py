import json
import sys
from datetime import datetime, timedelta
from typing import Dict
import pytz
from kexp_client import KexpClient
from spotify_client import SpotifyClient
from config import LOG_FILE, SHOW_END_HOUR


class PlaylistSyncer:
    def __init__(self):
        self.kexp_client = KexpClient()
        self.spotify_client = SpotifyClient()

    def sync_show_to_playlist(self, show_date: datetime, playlist_id: str = None) -> Dict:
        """
        Main sync function - gets KEXP songs and adds them to Spotify playlist.
        Creates a new playlist if playlist_id is not provided.
        """
        print(f"Starting sync for show on {show_date.strftime('%Y-%m-%d')}")

        # Get songs from KEXP
        print("Fetching songs from KEXP...")
        kexp_songs = self.kexp_client.get_show_songs(show_date)

        if not kexp_songs:
            print("No songs found for this date")
            return {"success": False, "error": "No songs found"}

        # Create playlist if not provided
        if not playlist_id:
            playlist_name = f"KEXP {show_date.strftime('%Y-%m-%d')}"
            playlist_description = f"Songs from KEXP show on {show_date.strftime('%B %d, %Y')}"
            try:
                playlist_id = self.spotify_client.create_playlist(playlist_name, playlist_description)
            except Exception as e:
                return {"success": False, "error": f"Failed to create playlist: {e}"}

        # Get existing tracks to avoid duplicates
        print("Checking existing playlist tracks...")
        existing_track_ids = set(self.spotify_client.get_playlist_tracks(playlist_id))

        # Search and collect new tracks
        print("Searching for songs on Spotify...")
        found_tracks = []
        not_found = []
        duplicates_skipped = []

        for song in kexp_songs:
            print(f"Searching: {song['artist']} - {song['song']}")

            spotify_track = self.spotify_client.search_track(
                song['song'],
                song['artist'],
                song['album']
            )

            if spotify_track:
                track_id = spotify_track['id']

                if track_id in existing_track_ids:
                    print(f"  Already in playlist")
                    duplicates_skipped.append({
                        'kexp_song': song,
                        'spotify_track': spotify_track
                    })
                else:
                    print(f"  Found: {spotify_track['artists'][0]['name']} - {spotify_track['name']}")
                    found_tracks.append({
                        'kexp_song': song,
                        'spotify_track': spotify_track
                    })
                    existing_track_ids.add(track_id)
            else:
                print(f"  Not found on Spotify")
                not_found.append(song)

        # Add new tracks to playlist
        if found_tracks:
            print(f"\nAdding {len(found_tracks)} new tracks to playlist...")
            track_ids = [track['spotify_track']['id'] for track in found_tracks]
            success = self.spotify_client.add_tracks_to_playlist(playlist_id, track_ids)

            if not success:
                return {"success": False, "error": "Failed to add tracks to playlist"}
        else:
            print("No new tracks to add")

        # Create summary
        summary = {
            "success": True,
            "show_date": show_date.isoformat(),
            "playlist_id": playlist_id,
            "total_kexp_songs": len(kexp_songs),
            "found_on_spotify": len(found_tracks),
            "not_found": len(not_found),
            "duplicates_skipped": len(duplicates_skipped),
            "tracks_added": len(found_tracks)
        }

        detailed_log = {
            **summary,
            "found_tracks": found_tracks,
            "not_found_tracks": not_found,
            "duplicates_skipped": duplicates_skipped,
            "timestamp": datetime.now().isoformat()
        }

        self._save_log(detailed_log)
        self._print_summary(summary)

        return summary

    def _save_log(self, log_data: Dict):
        """Save detailed log to file"""
        try:
            try:
                with open(LOG_FILE, 'r') as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                logs = []

            logs.append(log_data)

            with open(LOG_FILE, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

        except Exception as e:
            print(f"Warning: Could not save log file: {e}")

    def _print_summary(self, summary: Dict):
        """Print a summary of the sync operation"""
        print("\n" + "="*50)
        print("SYNC SUMMARY")
        print("="*50)
        print(f"Show Date: {summary['show_date']}")
        print(f"Total KEXP Songs: {summary['total_kexp_songs']}")
        print(f"Found on Spotify: {summary['found_on_spotify']}")
        print(f"Not Found: {summary['not_found']}")
        print(f"Duplicates Skipped: {summary['duplicates_skipped']}")
        print(f"New Tracks Added: {summary['tracks_added']}")
        print(f"Playlist ID: {summary['playlist_id']}")
        print("="*50)


def get_last_wednesday() -> datetime:
    """Get the date of the most recent Wednesday (in Pacific time)."""
    pacific = pytz.timezone('America/Los_Angeles')
    now_pacific = datetime.now(pacific)
    days_since_wednesday = (now_pacific.weekday() - 2) % 7
    if days_since_wednesday == 0 and now_pacific.hour < SHOW_END_HOUR:
        days_since_wednesday = 7  # If it's Wednesday but show hasn't ended, use last week
    target = now_pacific - timedelta(days=days_since_wednesday)
    return target.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def main():
    """Main function for command line usage.

    Usage:
        python main.py                    # Sync last Wednesday's show to a new playlist
        python main.py 2025-09-03         # Sync a specific date
        python main.py 2025-09-03 PLAYLIST_ID  # Sync to an existing playlist
    """
    syncer = PlaylistSyncer()

    # Parse date argument or default to last Wednesday
    if len(sys.argv) > 1:
        try:
            show_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {sys.argv[1]} (use YYYY-MM-DD)")
            sys.exit(1)
    else:
        show_date = get_last_wednesday()

    # Optional playlist ID argument
    playlist_id = sys.argv[2] if len(sys.argv) > 2 else None

    print("KEXP to Spotify Playlist Syncer")
    print("=" * 30)
    print(f"Show date: {show_date.strftime('%A, %B %d, %Y')}")
    if playlist_id:
        print(f"Target playlist: {playlist_id}")
    else:
        print("Will create a new playlist")
    print()

    result = syncer.sync_show_to_playlist(show_date, playlist_id)

    if result['success']:
        print(f"\nSync completed successfully!")
    else:
        print(f"\nSync failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
