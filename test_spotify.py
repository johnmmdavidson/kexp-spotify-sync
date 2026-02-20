from spotify_client import SpotifyClient


def test_spotify_search():
    """Test function to validate Spotify search"""
    client = SpotifyClient()

    test_songs = [
        {"song": "Glitter\u2010Shot", "artist": "Osees", "album": "Abomination Revealed at Last"},
        {"song": "I Want What I Want", "artist": "ORB", "album": "The Space Between"},
        {"song": "Rolling Greed", "artist": "Primitive Ring", "album": "Rolling Greed"},
    ]

    print("Testing Spotify search...")
    for test in test_songs:
        result = client.search_track(test['song'], test['artist'], test['album'])
        if result:
            print(f"  Found: {result['artists'][0]['name']} - {result['name']}")
            print(f"  Spotify ID: {result['id']}")
        else:
            print(f"  Not found: {test['artist']} - {test['song']}")
        print()


if __name__ == "__main__":
    test_spotify_search()
