import requests
from datetime import datetime, timedelta


class KexpShows:
    BASE_URL = "https://api.kexp.org/v2"

    def list_programs(self) -> list[dict]:
        """Fetch all active KEXP programs, sorted alphabetically by name."""
        programs = []
        offset = 0
        limit = 100

        while True:
            response = requests.get(
                f"{self.BASE_URL}/programs/",
                params={"limit": limit, "offset": offset},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            for prog in results:
                if prog.get("is_active"):
                    programs.append({
                        "id": prog["id"],
                        "name": prog["name"],
                        "tags": prog.get("tags", ""),
                    })

            if not data.get("next"):
                break
            offset += limit

        programs.sort(key=lambda p: p["name"].lower())
        return programs

    def get_episodes(self, program_id: int, limit: int = 10, offset: int = 0,
                     start_after: datetime | None = None,
                     start_before: datetime | None = None) -> tuple[list[dict], int]:
        """Fetch recent episodes for a program, most recent first.

        The KEXP shows API doesn't support server-side program filtering,
        so we paginate through shows and filter client-side. When
        start_after/start_before are provided, we narrow the server-side
        window via start_time_after/start_time_before so we don't have to
        scan the entire catalog.

        Returns (episodes, total_matched) where total_matched is the number
        found so far (not a global count, since we can't know that without
        scanning all shows).
        """
        matched = []
        api_offset = 0
        batch_size = 200
        max_scanned = 5000  # safety limit

        params_base = {"ordering": "-start_time", "limit": batch_size}
        if start_after is not None:
            params_base["start_time_after"] = start_after.strftime("%Y-%m-%dT%H:%M:%SZ")
        if start_before is not None:
            params_base["start_time_before"] = start_before.strftime("%Y-%m-%dT%H:%M:%SZ")

        while len(matched) < offset + limit and api_offset < max_scanned:
            response = requests.get(
                f"{self.BASE_URL}/shows/",
                params={**params_base, "offset": api_offset},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            if not results:
                break

            for show in results:
                if show.get("program") == program_id:
                    matched.append({
                        "id": show["id"],
                        "program_name": show.get("program_name", ""),
                        "host_names": show.get("host_names", []),
                        "start_time": show.get("start_time", ""),
                        "tagline": show.get("tagline", ""),
                    })

            if not data.get("next"):
                break
            api_offset += batch_size

        page = matched[offset:offset + limit]
        return page, len(matched)

    def get_show_details(self, show_id: int) -> dict:
        """Fetch full metadata for a single show instance."""
        response = requests.get(
            f"{self.BASE_URL}/shows/{show_id}/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def find_program_by_name(self, name: str) -> dict | None:
        """Find a program by case-insensitive name match."""
        programs = self.list_programs()
        name_lower = name.lower()

        # Exact match first
        for prog in programs:
            if prog["name"].lower() == name_lower:
                return prog

        # Substring match fallback
        for prog in programs:
            if name_lower in prog["name"].lower():
                return prog

        return None
