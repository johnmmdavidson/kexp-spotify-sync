import requests
import pytz
from datetime import datetime, timedelta
from typing import List, Dict
from config import SHOW_START_HOUR, SHOW_END_HOUR, KEXP_PLAYLIST_LOCATION


class KexpClient:
    def __init__(self):
        self.base_url = "https://api.kexp.org/v2/plays/"
        self.pacific_tz = pytz.timezone('America/Los_Angeles')
    
    def get_show_songs(self, date: datetime) -> List[Dict]:
        """
        Get all songs from the show for a given date.
        Date should be a datetime object for the Wednesday show date.
        """
        # Calculate show time window in Pacific time
        show_date = date.replace(hour=SHOW_START_HOUR, minute=0, second=0, microsecond=0)
        show_start = self.pacific_tz.localize(show_date)
        show_end = show_start + timedelta(hours=(SHOW_END_HOUR - SHOW_START_HOUR))
        
        # Convert to UTC for API request
        show_start_utc = show_start.astimezone(pytz.UTC)
        show_end_utc = show_end.astimezone(pytz.UTC)
        
        print(f"Fetching songs from {show_start} to {show_end} Pacific")
        print(f"UTC window: {show_start_utc} to {show_end_utc}")
        
        all_songs = []
        offset = 0
        limit = 100
        
        while True:
            # Build API request
            params = {
                'limit': limit,
                'airdate_after': show_start_utc.isoformat(),
                'ordering': 'airdate',
                'offset': offset,
                'playlist_location': KEXP_PLAYLIST_LOCATION
            }
            
            print(f"Fetching offset {offset}...")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break
                
            # Filter songs within our time window
            for item in results:
                airdate_str = item.get('airdate')
                if not airdate_str:
                    continue
                    
                # Parse airdate
                airdate = datetime.fromisoformat(airdate_str.replace('Z', '+00:00'))
                
                # Check if within our show window
                if airdate >= show_end_utc:
                    # We've gone past our show window, stop fetching
                    return self._filter_songs(all_songs)
                    
                if show_start_utc <= airdate < show_end_utc:
                    all_songs.append(item)
            
            # Check if we have more data or if we've passed our time window
            if not data.get('next') or len(results) < limit:
                break
                
            offset += limit
        
        return self._filter_songs(all_songs)
    
    def _filter_songs(self, songs: List[Dict]) -> List[Dict]:
        """Filter to only actual track plays (not airbreaks)"""
        filtered_songs = []
        
        for song in songs:
            # Only include actual track plays
            if song.get('play_type') != 'trackplay':
                continue
                
            # Must have song and artist
            if not song.get('song') or not song.get('artist'):
                continue
                
            # Extract clean data
            clean_song = {
                'song': song['song'].strip(),
                'artist': song['artist'].strip(),
                'album': song.get('album', '').strip(),
                'airdate': song['airdate'],
                'kexp_id': song['id']
            }
            
            filtered_songs.append(clean_song)
        
        print(f"Found {len(filtered_songs)} tracks from the show")
        return filtered_songs
