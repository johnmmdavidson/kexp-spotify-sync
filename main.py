import argparse
import json
import sys
from datetime import datetime

from kexp_client import KexpClient
from kexp_shows import KexpShows
from config import LOG_FILE


class PlaylistSyncer:
    def __init__(self, dry_run: bool = False):
        self.kexp_client = KexpClient()
        if dry_run:
            self.spotify_client = None
        else:
            from spotify_client import SpotifyClient
            self.spotify_client = SpotifyClient()

    def sync_show_to_playlist(self, show_id: int, program_name: str,
                              show_date: str, host_names: str = "",
                              playlist_id: str = None, dry_run: bool = False) -> dict:
        """Fetch songs for a show episode and add them to a Spotify playlist."""
        mode_label = "[DRY RUN] " if dry_run else ""
        print(f"{mode_label}Starting sync for {program_name} on {show_date}")

        kexp_songs = self.kexp_client.get_show_songs(show_id)

        if not kexp_songs:
            print("No songs found for this episode")
            return {"success": False, "error": "No songs found"}

        if dry_run:
            return self._dry_run(kexp_songs, program_name, show_date, show_id)

        if not playlist_id:
            playlist_name = f"{program_name} (KEXP) - {show_date}"
            host_part = f" with {host_names}" if host_names else ""
            playlist_description = f"Playlist from {show_date} edition of {program_name}{host_part} on KEXP"
            try:
                playlist_id = self.spotify_client.create_playlist(playlist_name, playlist_description)
            except Exception as e:
                return {"success": False, "error": f"Failed to create playlist: {e}"}

        print("Checking existing playlist tracks...")
        existing_track_ids = set(self.spotify_client.get_playlist_tracks(playlist_id))

        print("Searching for songs on Spotify...")
        found_tracks = []
        not_found = []
        duplicates_skipped = []

        for song in kexp_songs:
            print(f"Searching: {song['artist']} - {song['song']}")

            spotify_track = self.spotify_client.search_track(
                song['song'], song['artist'], song['album']
            )

            if spotify_track:
                track_id = spotify_track['id']
                if track_id in existing_track_ids:
                    print("  Already in playlist")
                    duplicates_skipped.append({
                        'kexp_song': song, 'spotify_track': spotify_track
                    })
                else:
                    print(f"  Found: {spotify_track['artists'][0]['name']} - {spotify_track['name']}")
                    found_tracks.append({
                        'kexp_song': song, 'spotify_track': spotify_track
                    })
                    existing_track_ids.add(track_id)
            else:
                print("  Not found on Spotify")
                not_found.append(song)

        if found_tracks:
            print(f"\nAdding {len(found_tracks)} new tracks to playlist...")
            track_ids = [t['spotify_track']['id'] for t in found_tracks]
            success = self.spotify_client.add_tracks_to_playlist(playlist_id, track_ids)
            if not success:
                return {"success": False, "error": "Failed to add tracks to playlist"}
        else:
            print("No new tracks to add")

        summary = {
            "success": True,
            "program_name": program_name,
            "show_date": show_date,
            "show_id": show_id,
            "playlist_id": playlist_id,
            "total_kexp_songs": len(kexp_songs),
            "found_on_spotify": len(found_tracks),
            "not_found": len(not_found),
            "duplicates_skipped": len(duplicates_skipped),
            "tracks_added": len(found_tracks),
        }

        detailed_log = {
            **summary,
            "found_tracks": found_tracks,
            "not_found_tracks": not_found,
            "duplicates_skipped": duplicates_skipped,
            "timestamp": datetime.now().isoformat(),
        }

        self._save_log(detailed_log)
        self._print_summary(summary)
        return summary

    def _save_log(self, log_data: dict):
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

    def _print_summary(self, summary: dict):
        print("\n" + "=" * 50)
        print("SYNC SUMMARY")
        print("=" * 50)
        print(f"Program: {summary['program_name']}")
        print(f"Show Date: {summary['show_date']}")
        print(f"Total KEXP Songs: {summary['total_kexp_songs']}")
        print(f"Found on Spotify: {summary['found_on_spotify']}")
        print(f"Not Found: {summary['not_found']}")
        print(f"Duplicates Skipped: {summary['duplicates_skipped']}")
        print(f"New Tracks Added: {summary['tracks_added']}")
        print(f"Playlist ID: {summary['playlist_id']}")
        print("=" * 50)

    def _dry_run(self, kexp_songs: list, program_name: str,
                 show_date: str, show_id: int) -> dict:
        """Print what would be synced without touching Spotify."""
        print(f"\n[DRY RUN] {len(kexp_songs)} tracks from KEXP:\n")
        for i, song in enumerate(kexp_songs, 1):
            album = f"  [{song['album']}]" if song.get("album") else ""
            print(f"  {i:2}. {song['artist']} - {song['song']}{album}")

        print(f"\n[DRY RUN] No Spotify playlist created or modified.")

        summary = {
            "success": True,
            "dry_run": True,
            "program_name": program_name,
            "show_date": show_date,
            "show_id": show_id,
            "total_kexp_songs": len(kexp_songs),
        }
        self._save_log({**summary, "tracks": kexp_songs, "timestamp": datetime.now().isoformat()})
        return summary


def format_episode_date(start_time: str) -> str:
    """Parse ISO start_time into a readable date string."""
    try:
        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y").replace(" 0", " ")
    except (ValueError, AttributeError):
        return start_time


def interactive_mode(dry_run: bool = False):
    """Browse programs, pick an episode, and sync it."""
    shows = KexpShows()

    # List programs
    print("Fetching KEXP programs...\n")
    programs = shows.list_programs()

    if not programs:
        print("No active programs found.")
        sys.exit(1)

    print("Active KEXP Programs:")
    print("-" * 40)
    for i, prog in enumerate(programs, 1):
        tags = f"  ({prog['tags']})" if prog.get("tags") else ""
        print(f"  {i:2}. {prog['name']}{tags}")

    print()
    try:
        choice = input("Select a program number (or q to quit): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    if choice.lower() == "q":
        sys.exit(0)

    try:
        idx = int(choice) - 1
        if not (0 <= idx < len(programs)):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        sys.exit(1)

    program = programs[idx]
    print(f"\nSelected: {program['name']}")

    # Browse episodes with pagination
    page_size = 10
    offset = 0

    while True:
        print(f"\nFetching episodes...")
        episodes, total = shows.get_episodes(program["id"], limit=page_size, offset=offset)

        if not episodes:
            print("No episodes found for this program.")
            sys.exit(1)

        print(f"\nRecent episodes of {program['name']} ({offset + 1}-{offset + len(episodes)} of {total}):")
        print("-" * 50)
        for i, ep in enumerate(episodes, 1):
            date_str = format_episode_date(ep["start_time"])
            hosts = ", ".join(ep["host_names"]) if ep.get("host_names") else "Unknown host"
            print(f"  {i:2}. {date_str}  -  {hosts}")

        print()
        has_next = (offset + page_size) < total
        has_prev = offset > 0
        nav = []
        if has_next:
            nav.append("[N]ext")
        if has_prev:
            nav.append("[P]revious")
        nav.append("[Q]uit")
        nav_str = " / ".join(nav)

        try:
            choice = input(f"Select episode number, or {nav_str}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice.lower() == "q":
            sys.exit(0)
        elif choice.lower() == "n" and has_next:
            offset += page_size
            continue
        elif choice.lower() == "p" and has_prev:
            offset -= page_size
            continue

        try:
            ep_idx = int(choice) - 1
            if not (0 <= ep_idx < len(episodes)):
                raise ValueError
        except ValueError:
            print("Invalid selection.")
            continue

        episode = episodes[ep_idx]
        break

    show_date = format_episode_date(episode["start_time"])
    hosts = ", ".join(episode["host_names"]) if episode.get("host_names") else "Unknown host"

    print(f"\n{'=' * 50}")
    print(f"Program:  {program['name']}")
    print(f"Episode:  {show_date}")
    print(f"Host(s):  {hosts}")
    print(f"{'=' * 50}")

    try:
        confirm = input("\nSync this episode to Spotify? [Y/n]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    if confirm.lower() not in ("", "y", "yes"):
        print("Cancelled.")
        sys.exit(0)

    syncer = PlaylistSyncer(dry_run=dry_run)
    result = syncer.sync_show_to_playlist(
        show_id=episode["id"],
        program_name=program["name"],
        show_date=show_date,
        host_names=hosts,
        dry_run=dry_run,
    )
    return result


def direct_mode(args):
    """Sync using CLI arguments."""
    shows = KexpShows()

    # Find the program
    program = shows.find_program_by_name(args.show)
    if not program:
        print(f"Program not found: '{args.show}'")
        print("Use --list to see available programs.")
        sys.exit(1)

    print(f"Program: {program['name']}")

    if args.latest:
        # Grab the most recent episode
        episodes, _ = shows.get_episodes(program["id"], limit=1)
        if not episodes:
            print("No episodes found for this program.")
            sys.exit(1)
        best = episodes[0]
    elif args.date:
        # Find the episode closest to the given date
        try:
            target = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: '{args.date}' (use YYYY-MM-DD)")
            sys.exit(1)
        # Fetch a large window so older dates still match correctly
        episodes, _ = shows.get_episodes(program["id"], limit=200)
        if not episodes:
            print("No episodes found for this program.")
            sys.exit(1)
        best = None
        best_diff = None
        for ep in episodes:
            try:
                ep_dt = datetime.fromisoformat(ep["start_time"].replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                continue
            diff = abs((ep_dt - target).total_seconds())
            if best_diff is None or diff < best_diff:
                best = ep
                best_diff = diff
        if not best:
            print("Could not find a matching episode.")
            sys.exit(1)
        # Warn if the closest match is far from the requested date (>7 days)
        if best_diff > 7 * 86400:
            matched_date = format_episode_date(best["start_time"])
            print(f"Warning: no episode near {args.date}, closest is {matched_date}")
    else:
        print("Direct mode requires --latest or --date.")
        sys.exit(1)

    show_date = format_episode_date(best["start_time"])
    hosts = ", ".join(best["host_names"]) if best.get("host_names") else "Unknown host"
    print(f"Episode:  {show_date}  -  {hosts}")

    syncer = PlaylistSyncer(dry_run=args.dry_run)
    result = syncer.sync_show_to_playlist(
        show_id=best["id"],
        program_name=program["name"],
        show_date=show_date,
        host_names=hosts,
        playlist_id=args.playlist,
        dry_run=args.dry_run,
    )
    return result


def list_programs():
    """Print all active programs and exit."""
    shows = KexpShows()
    programs = shows.list_programs()
    print("Active KEXP Programs:")
    print("-" * 40)
    for prog in programs:
        tags = f"  ({prog['tags']})" if prog.get("tags") else ""
        print(f"  {prog['name']}{tags}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync KEXP radio show playlists to Spotify"
    )
    parser.add_argument(
        "--show", type=str,
        help="Program name (e.g. 'Astral Plane'). Starts interactive mode if omitted."
    )
    parser.add_argument(
        "--latest", action="store_true",
        help="Sync the most recent episode. Ideal for cron jobs."
    )
    parser.add_argument(
        "--date", type=str,
        help="Episode date to sync (YYYY-MM-DD). Finds closest episode."
    )
    parser.add_argument(
        "--playlist", type=str,
        help="Existing Spotify playlist ID to sync into (creates new if omitted)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Fetch KEXP tracks and show what would be synced without creating/modifying Spotify playlists."
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all active KEXP programs and exit."
    )

    args = parser.parse_args()

    print()
    print(" \u2588\u2588   \u2588\u2588 \u2588\u2588\u2588\u2588\u2588\u2588\u2588 \u2588\u2588   \u2588\u2588 \u2588\u2588\u2588\u2588\u2588\u2588")
    print(" \u2588\u2588  \u2588\u2588  \u2588\u2588       \u2588\u2588 \u2588\u2588  \u2588\u2588   \u2588\u2588")
    print(" \u2588\u2588\u2588\u2588\u2588   \u2588\u2588\u2588\u2588\u2588     \u2588\u2588\u2588   \u2588\u2588\u2588\u2588\u2588\u2588")
    print(" \u2588\u2588  \u2588\u2588  \u2588\u2588       \u2588\u2588 \u2588\u2588  \u2588\u2588")
    print(" \u2588\u2588   \u2588\u2588 \u2588\u2588\u2588\u2588\u2588\u2588\u2588 \u2588\u2588   \u2588\u2588 \u2588\u2588")
    print(" \u2500\u2500\u2500\u2500\u2500\u2500\u2500 spotify sync \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print()

    if args.list:
        list_programs()
        sys.exit(0)

    if args.show:
        result = direct_mode(args)
    else:
        result = interactive_mode(dry_run=args.dry_run)

    if result["success"]:
        print("\nSync completed successfully!")
    else:
        print(f"\nSync failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
