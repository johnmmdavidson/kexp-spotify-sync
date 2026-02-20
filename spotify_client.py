import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional
import re
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
)


class SpotifyClient:
    def __init__(self):
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise RuntimeError(
                "Missing Spotify credentials. "
                "Create a .env file with SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )

        # Set up OAuth with required scopes
        self.scope = "playlist-modify-public playlist-modify-private playlist-read-private user-read-private"

        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=self.scope,
            cache_path=".spotify_cache"
        )

        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_user_id(self) -> str:
        """Get the current user's Spotify ID"""
        user = self.sp.current_user()
        return user['id']

    def create_playlist(self, name: str, description: str = "") -> str:
        """Create a new playlist and return its ID.

        Uses POST /me/playlists (the Feb 2026 replacement for
        the removed POST /users/{id}/playlists endpoint).
        """
        data = {
            "name": name,
            "public": False,
            "collaborative": False,
            "description": description
        }
        playlist = self.sp._post("me/playlists", payload=data)
        print(f"Created playlist: {playlist['name']} (ID: {playlist['id']})")
        return playlist['id']

    def search_track(self, song: str, artist: str, album: str = "") -> Optional[Dict]:
        """
        Search for a track on Spotify using multiple strategies.
        Returns the best match or None if not found.

        Note: search limit max is now 10 per the Feb 2026 API changes.
        """
        # Clean up search terms
        clean_song = self._clean_search_term(song)
        clean_artist = self._clean_search_term(artist)

        # Strategy 1: Artist and track specific search
        query1 = f'track:"{clean_song}" artist:"{clean_artist}"'
        result = self._try_search(query1)
        if result:
            return result

        # Strategy 2: Simple artist + song search
        query2 = f'"{clean_artist}" "{clean_song}"'
        result = self._try_search(query2)
        if result:
            return result

        # Strategy 3: Just the song title (fallback)
        query3 = f'"{clean_song}"'
        result = self._try_search(query3)
        if result:
            # Verify artist similarity for fallback matches
            if self._artist_similarity(clean_artist, result['artists'][0]['name']) > 0.5:
                return result

        return None

    def _try_search(self, query: str) -> Optional[Dict]:
        """Try a single search query"""
        try:
            results = self.sp.search(q=query, type='track', limit=10)
            tracks = results['tracks']['items']

            if tracks:
                return tracks[0]

        except Exception as e:
            print(f"Search error for '{query}': {e}")

        return None

    def _clean_search_term(self, term: str) -> str:
        """Clean up search terms for better matching"""
        term = re.sub(r'\s*\(.*?\)\s*', ' ', term)  # Remove parentheses content
        term = re.sub(r'\s*\[.*?\]\s*', ' ', term)  # Remove bracket content
        term = re.sub(r'\s*feat\.?\s+.*', '', term, flags=re.IGNORECASE)
        term = re.sub(r'\s*ft\.?\s+.*', '', term, flags=re.IGNORECASE)
        term = re.sub(r'\s+', ' ', term)  # Normalize whitespace
        return term.strip()

    def _artist_similarity(self, artist1: str, artist2: str) -> float:
        """Simple artist name similarity check"""
        a1 = artist1.lower().strip()
        a2 = artist2.lower().strip()

        if a1 == a2:
            return 1.0
        if a1 in a2 or a2 in a1:
            return 0.8

        words1 = set(a1.split())
        words2 = set(a2.split())
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        return overlap / total if total > 0 else 0.0

    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """Get all track IDs currently in a playlist.

        Uses GET /playlists/{id}/items (renamed from /tracks in Feb 2026).
        """
        plid = self.sp._get_id("playlist", playlist_id)
        track_ids = []
        offset = 0
        limit = 100

        while True:
            results = self.sp._get(
                f"playlists/{plid}/items",
                limit=limit,
                offset=offset,
                fields="items.track.id,next",
                additional_types="track"
            )

            for item in results.get('items', []):
                if item.get('track') and item['track'].get('id'):
                    track_ids.append(item['track']['id'])

            if not results.get('next'):
                break
            offset += limit

        return track_ids

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to playlist in batches of 100.

        Uses POST /playlists/{id}/items (renamed from /tracks in Feb 2026).
        """
        if not track_ids:
            return True

        plid = self.sp._get_id("playlist", playlist_id)

        try:
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                uris = [f"spotify:track:{tid}" for tid in batch]
                self.sp._post(f"playlists/{plid}/items", payload={"uris": uris})
            return True
        except Exception as e:
            print(f"Error adding tracks to playlist: {e}")
            return False
