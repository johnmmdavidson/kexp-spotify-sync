import requests
from kexp_shows import KexpShows


class KexpClient:
    BASE_URL = "https://api.kexp.org/v2"

    def __init__(self):
        self._shows = KexpShows()

    def get_show_songs(self, show_id: int) -> list[dict]:
        """Get all songs from a specific show episode by its ID.

        Fetches the show's start_time, then queries plays starting from
        that time and filters to only plays belonging to this show.
        """
        show = self._shows.get_show_details(show_id)
        start_time = show["start_time"]
        print(f"Fetching songs for {show.get('program_name', 'show')} on {start_time[:10]}...")

        all_plays = []
        offset = 0
        limit = 100
        found_our_show = False

        while True:
            params = {
                "airdate_after": start_time,
                "ordering": "airdate",
                "limit": limit,
                "offset": offset,
            }

            response = requests.get(
                f"{self.BASE_URL}/plays/",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                break

            for play in results:
                if play.get("show") == show_id:
                    all_plays.append(play)
                    found_our_show = True
                elif found_our_show:
                    # We've moved past our show into the next one
                    return self._filter_songs(all_plays)

            if not data.get("next"):
                break
            offset += limit

        return self._filter_songs(all_plays)

    def _filter_songs(self, songs: list[dict]) -> list[dict]:
        """Filter to only actual track plays (not airbreaks)."""
        filtered_songs = []

        for song in songs:
            if song.get("play_type") != "trackplay":
                continue

            if not song.get("song") or not song.get("artist"):
                continue

            clean_song = {
                "song": song["song"].strip(),
                "artist": song["artist"].strip(),
                "album": (song.get("album") or "").strip(),
                "airdate": song["airdate"],
                "kexp_id": song["id"],
            }

            filtered_songs.append(clean_song)

        print(f"Found {len(filtered_songs)} tracks from the show")
        return filtered_songs
