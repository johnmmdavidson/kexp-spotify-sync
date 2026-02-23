from kexp_client import KexpClient
from kexp_shows import KexpShows


def test_list_programs():
    """List all active KEXP programs."""
    shows = KexpShows()
    programs = shows.list_programs()
    print(f"Found {len(programs)} active programs:\n")
    for prog in programs:
        tags = f"  ({prog['tags']})" if prog.get("tags") else ""
        print(f"  [{prog['id']}] {prog['name']}{tags}")


def test_get_episodes(program_name="Astral Plane"):
    """Fetch recent episodes for a program."""
    shows = KexpShows()
    program = shows.find_program_by_name(program_name)
    if not program:
        print(f"Program not found: {program_name}")
        return

    print(f"\nRecent episodes of {program['name']}:\n")
    episodes, total = shows.get_episodes(program["id"], limit=5)
    for ep in episodes:
        hosts = ", ".join(ep["host_names"]) if ep.get("host_names") else "Unknown"
        print(f"  [{ep['id']}] {ep['start_time'][:10]}  -  {hosts}")

    return episodes


def test_get_songs(program_name="Astral Plane"):
    """Fetch songs from the most recent episode of a program."""
    shows = KexpShows()
    program = shows.find_program_by_name(program_name)
    if not program:
        print(f"Program not found: {program_name}")
        return

    episodes, _ = shows.get_episodes(program["id"], limit=1)
    if not episodes:
        print("No episodes found")
        return

    episode = episodes[0]
    print(f"\nFetching songs from {program['name']} on {episode['start_time'][:10]}...\n")

    client = KexpClient()
    songs = client.get_show_songs(episode["id"])

    print(f"Found {len(songs)} songs:")
    for i, song in enumerate(songs[:10], 1):
        print(f"  {i}. {song['artist']} - {song['song']}")
        if song["album"]:
            print(f"     Album: {song['album']}")

    if len(songs) > 10:
        print(f"  ... and {len(songs) - 10} more")

    return songs


if __name__ == "__main__":
    test_list_programs()
    print()
    test_get_episodes()
    print()
    test_get_songs()
