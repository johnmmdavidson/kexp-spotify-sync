from datetime import datetime
from kexp_client import KexpClient


def test_kexp_client():
    """Test function to validate our KEXP client"""
    client = KexpClient()

    # Test with September 3, 2025
    test_date = datetime(2025, 9, 3)  # Wednesday
    songs = client.get_show_songs(test_date)

    print(f"\nFound {len(songs)} songs:")
    for i, song in enumerate(songs[:10]):  # Show first 10
        print(f"{i+1}. {song['artist']} - {song['song']}")
        if song['album']:
            print(f"   Album: {song['album']}")
        print(f"   Aired: {song['airdate']}")
        print()

    if len(songs) > 10:
        print(f"... and {len(songs) - 10} more songs")

    return songs


if __name__ == "__main__":
    test_kexp_client()
