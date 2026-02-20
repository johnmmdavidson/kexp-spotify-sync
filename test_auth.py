from spotify_client import SpotifyClient

print("Testing Spotify authentication...")
print()

try:
    client = SpotifyClient()
    user = client.sp.current_user()
    print(f"Authentication successful!")
    print(f"  User: {user['display_name']}")
    print(f"  ID:   {user['id']}")

    # Test search (uses GET /search)
    results = client.sp.search("KEXP", type='track', limit=1)
    print(f"  Search: OK")

    # Test playlist listing (uses GET /me/playlists)
    playlists = client.sp.current_user_playlists(limit=1)
    print(f"  Playlists: OK ({playlists['total']} total)")

    print()
    print("All checks passed - ready to sync!")

except Exception as e:
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Make sure .env has your new app's SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    print("  2. Make sure the redirect URI in your Spotify app settings matches: http://127.0.0.1:8080/callback")
    print("  3. Delete .spotify_cache if it exists and try again")
