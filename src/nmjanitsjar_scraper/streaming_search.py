"""Utilities for discovering streaming links for NM Janitsjar performances.

This module provides helper classes that talk to Spotify and Apple Music
and attempts to map competition pieces to their corresponding album tracks.

Usage example:

```
poetry run python -m src.nmjanitsjar_scraper.streaming_search \
    --positions apps/band-positions/public/data/band_positions.json \
    --output data/processed/piece_streaming_links.json
```

Spotify credentials are read from the ``SPOTIFY_CLIENT_ID`` and
``SPOTIFY_CLIENT_SECRET`` environment variables unless explicitly
provided via command-line options.
"""

from __future__ import annotations

import base64
import json
import os
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from requests import Response, Session
try:
    from tenacity import retry, stop_after_attempt, wait_fixed  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback when tenacity is unavailable
    def retry(*_args, **_kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

    def stop_after_attempt(_attempts):  # type: ignore
        return None

    def wait_fixed(_seconds):  # type: ignore
        return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def _strip_parenthetical(value: str) -> str:
    result = []
    depth = 0
    for char in value:
        if char == "(":
            depth += 1
        elif char == ")":
            if depth > 0:
                depth -= 1
            continue
        elif depth > 0:
            continue
        result.append(char)
    return "".join(result)


def normalize_title(value: str) -> str:
    """Normalize a piece or track title for fuzzy comparison."""

    if not value:
        return ""

    cleaned = (
        value.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    cleaned = _strip_parenthetical(cleaned)
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    cleaned = cleaned.lower()
    tokens = []
    current = []
    for ch in cleaned:
        if ch.isalnum():
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return "-".join(tokens)


def similarity_score(piece_slug: str, track_slug: str) -> float:
    if not piece_slug or not track_slug:
        return 0.0
    if piece_slug == track_slug:
        return 1.0
    matcher = SequenceMatcher(None, piece_slug, track_slug)
    ratio = matcher.ratio()
    tokens_piece = set(piece_slug.split("-"))
    tokens_track = set(track_slug.split("-"))
    if not tokens_piece or not tokens_track:
        token_overlap = 0.0
    else:
        token_overlap = len(tokens_piece & tokens_track) / max(len(tokens_piece), len(tokens_track))
    if piece_slug in track_slug or track_slug in piece_slug:
        ratio = max(ratio, 0.9)
    return max(ratio, token_overlap)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Performance:
    year: int
    division: str
    band: str
    piece: str


@dataclass
class Track:
    platform: str
    title: str
    slug: str
    url: str
    album: str
    album_id: str
    match_score: float = 0.0


@dataclass
class StreamingMatch:
    performance: Performance
    spotify: Optional[Track] = None
    apple_music: Optional[Track] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        track = self.spotify or self.apple_music
        return {
            "year": self.performance.year,
            "division": self.performance.division,
            "band": self.performance.band,
            "result_piece": self.performance.piece,
            "recording_title": track.title if track else None,
            "album": track.album if track else None,
            "spotify": self.spotify.url if self.spotify else None,
            "apple_music": self.apple_music.url if self.apple_music else None,
        }


# ---------------------------------------------------------------------------
# Spotify client
# ---------------------------------------------------------------------------


class SpotifyClient:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_URL = "https://api.spotify.com/v1"

    def __init__(self, client_id: str, client_secret: str, *, session: Optional[Session] = None, market: str = "NO"):
        if not client_id or not client_secret:
            raise ValueError("Spotify client id and secret must be provided")
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session or requests.Session()
        self.market = market
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def _auth_header(self) -> Dict[str, str]:
        self._ensure_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    def _ensure_token(self) -> None:
        now = time.time()
        if self._access_token and now < self._token_expiry - 60:
            return

        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        response = self.session.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        self._token_expiry = now + expires_in

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _get(self, path: str, *, params: Optional[Dict[str, str]] = None) -> Response:
        url = f"{self.API_URL}{path}"
        headers = self._auth_header()
        response = self.session.get(url, headers=headers, params=params, timeout=15)
        if response.status_code >= 500:
            response.raise_for_status()
        if response.status_code == 401:
            self._access_token = None
            self._token_expiry = 0.0
            headers = self._auth_header()
            response = self.session.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response

    def search_albums(self, query: str, *, limit: int = 5) -> List[Dict]:
        params = {
            "q": query,
            "type": "album",
            "limit": limit,
        }
        if self.market:
            params["market"] = self.market
        data = self._get("/search", params=params).json()
        return data.get("albums", {}).get("items", [])

    def get_album_tracks(self, album_id: str) -> List[Dict]:
        items: List[Dict] = []
        params = {"limit": 50}
        while True:
            data = self._get(f"/albums/{album_id}/tracks", params=params).json()
            items.extend(data.get("items", []))
            next_url = data.get("next")
            if not next_url:
                break
            params = {"offset": len(items), "limit": 50}
        return items


# ---------------------------------------------------------------------------
# Apple Music (iTunes) client
# ---------------------------------------------------------------------------


class AppleMusicClient:
    SEARCH_URL = "https://itunes.apple.com/search"
    LOOKUP_URL = "https://itunes.apple.com/lookup"

    def __init__(self, *, country: str = "us", session: Optional[Session] = None):
        self.country = country
        self.session = session or requests.Session()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def search_album(self, term: str, limit: int = 5) -> List[Dict]:
        params = {
            "term": term,
            "entity": "album",
            "limit": limit,
            "country": self.country,
        }
        response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def lookup_album_tracks(self, collection_id: int) -> List[Dict]:
        params = {"id": collection_id, "entity": "song", "country": self.country}
        response = self.session.get(self.LOOKUP_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return [item for item in data.get("results", []) if item.get("wrapperType") == "track"]


# ---------------------------------------------------------------------------
# Streaming discovery logic
# ---------------------------------------------------------------------------


DIVISION_ALBUM_LABELS = {
    "Elite": "Elitedivisjon",
}


def resolve_album_search_terms(year: int, division: str) -> List[str]:
    normalized = DIVISION_ALBUM_LABELS.get(division, division)
    base = f"NM Janitsjar {year} {normalized}".strip()
    variants = {
        base,
        f"NM Janitsjar {year} {normalized} (Live)",
        f"NM Janitsjar {year} - {normalized}",
        f"NM Janitsjar {year}",
    }
    return [variant for variant in variants if variant]


def load_performances(path: Path, *, min_year: int = 2017) -> List[Performance]:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    performances: List[Performance] = []
    for band in dataset.get("bands", []):
        name = band.get("name")
        for entry in band.get("entries", []):
            year = entry.get("year")
            division = entry.get("division")
            pieces = entry.get("pieces") or []
            if not isinstance(pieces, list):
                pieces = [str(pieces)]
            if not isinstance(year, int) or year < min_year:
                continue
            for raw_piece in pieces:
                piece = (raw_piece or "").strip()
                if not piece:
                    continue
                performances.append(Performance(year=year, division=division, band=name, piece=piece))
    return performances


class StreamingLinkFinder:
    def __init__(
        self,
        *,
        spotify: Optional[SpotifyClient],
        apple_music: Optional[AppleMusicClient],
    ) -> None:
        self.spotify = spotify
        self.apple_music = apple_music
        self._spotify_album_cache: Dict[Tuple[int, str], List[Track]] = {}
        self._apple_album_cache: Dict[Tuple[int, str], List[Track]] = {}

    def build_links(self, performances: Iterable[Performance]) -> List[StreamingMatch]:
        matches: List[StreamingMatch] = []
        for performance in performances:
            spotify_track = self.match_spotify(performance)
            apple_track = self.match_apple(performance)
            match = StreamingMatch(performance=performance, spotify=spotify_track, apple_music=apple_track)
            matches.append(match)
        return matches

    # ----------------------- Spotify -----------------------

    def _get_spotify_tracks_for_division(self, year: int, division: str) -> List[Track]:
        key = (year, division)
        if key in self._spotify_album_cache:
            return self._spotify_album_cache[key]
        if not self.spotify:
            self._spotify_album_cache[key] = []
            return []

        tracks: List[Track] = []
        seen_albums: set[str] = set()

        for term in resolve_album_search_terms(year, division):
            albums = self.spotify.search_albums(term)
            for album in albums:
                album_id = album.get("id")
                album_name = album.get("name")
                if not album_id or album_id in seen_albums:
                    continue
                seen_albums.add(album_id)
                track_items = self.spotify.get_album_tracks(album_id)
                for item in track_items:
                    title = item.get("name")
                    external_urls = item.get("external_urls") or {}
                    url = external_urls.get("spotify")
                    if not title or not url:
                        continue
                    slug = normalize_title(title)
                    tracks.append(
                        Track(
                            platform="spotify",
                            title=title,
                            slug=slug,
                            url=url,
                            album=album_name or term,
                            album_id=album_id,
                        )
                    )
            if tracks:
                break

        self._spotify_album_cache[key] = tracks
        return tracks

    def match_spotify(self, performance: Performance) -> Optional[Track]:
        tracks = self._get_spotify_tracks_for_division(performance.year, performance.division)
        if not tracks:
            return None
        piece_slug = normalize_title(performance.piece)
        best_match: Optional[Track] = None
        best_score = 0.0
        for track in tracks:
            score = similarity_score(piece_slug, track.slug)
            if score > best_score:
                best_score = score
                best_match = track
        if best_match and best_score >= 0.65:
            best_match.match_score = best_score
            return best_match
        return None

    # ----------------------- Apple Music -----------------------

    def _get_apple_tracks_for_division(self, year: int, division: str) -> List[Track]:
        key = (year, division)
        if key in self._apple_album_cache:
            return self._apple_album_cache[key]
        if not self.apple_music:
            self._apple_album_cache[key] = []
            return []

        tracks: List[Track] = []
        seen_collections: set[int] = set()

        for term in resolve_album_search_terms(year, division):
            albums = self.apple_music.search_album(term)
            for album in albums:
                collection_id = album.get("collectionId")
                collection_name = album.get("collectionName")
                if not collection_id or collection_id in seen_collections:
                    continue
                seen_collections.add(collection_id)
                songs = self.apple_music.lookup_album_tracks(collection_id)
                for song in songs:
                    title = song.get("trackName")
                    url = song.get("trackViewUrl")
                    if not title or not url:
                        continue
                    slug = normalize_title(title)
                    tracks.append(
                        Track(
                            platform="apple_music",
                            title=title,
                            slug=slug,
                            url=url,
                            album=collection_name or term,
                            album_id=str(collection_id),
                        )
                    )
            if tracks:
                break

        self._apple_album_cache[key] = tracks
        return tracks

    def match_apple(self, performance: Performance) -> Optional[Track]:
        tracks = self._get_apple_tracks_for_division(performance.year, performance.division)
        if not tracks:
            return None
        piece_slug = normalize_title(performance.piece)
        best_match: Optional[Track] = None
        best_score = 0.0
        for track in tracks:
            score = similarity_score(piece_slug, track.slug)
            if score > best_score:
                best_score = score
                best_match = track
        if best_match and best_score >= 0.65:
            best_match.match_score = best_score
            return best_match
        return None


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------


def _load_credentials(credentials_path: Optional[Path], console) -> Tuple[Optional[str], Optional[str]]:
    if not credentials_path:
        return None, None
    credentials_path = credentials_path.expanduser()
    if not credentials_path.exists():
        return None, None
    try:
        data = json.loads(credentials_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[red]Kunne ikke tolke Spotify-nøkler fra {credentials_path}: {exc}[/red]")
        return None, None
    client_id = (data.get("spotify_client_id") or "").strip() or None
    client_secret = (data.get("spotify_client_secret") or "").strip() or None
    return client_id, client_secret


def generate_streaming_links(
    *,
    positions: Path,
    output: Path,
    min_year: int = 2017,
    spotify_client_id: Optional[str] = None,
    spotify_client_secret: Optional[str] = None,
    apple_country: str = "us",
    skip_spotify: bool = False,
    skip_apple: bool = False,
    credentials_path: Optional[Path] = None,
    console=None,
) -> int:
    from rich.console import Console
    from rich.progress import track

    console = console or Console()

    if not positions.exists():
        console.print(f"[red]Positions file not found:[/red] {positions}")
        raise FileNotFoundError(positions)

    spotify_client: Optional[SpotifyClient] = None
    apple_client: Optional[AppleMusicClient] = None

    if not skip_spotify:
        if not spotify_client_id or not spotify_client_secret:
            default_credentials_path = credentials_path or Path("config/streaming_credentials.json")
            file_client_id, file_client_secret = _load_credentials(default_credentials_path, console)
            spotify_client_id = spotify_client_id or file_client_id
            spotify_client_secret = spotify_client_secret or file_client_secret
            if file_client_id and file_client_secret:
                console.print(f"[green]Henter Spotify-nøkler fra {default_credentials_path}[/green]")

        if not spotify_client_id or not spotify_client_secret:
            console.print("[yellow]Spotify-nøkler mangler – hopper over Spotify-søk[/yellow]")
        else:
            spotify_client = SpotifyClient(client_id=spotify_client_id, client_secret=spotify_client_secret)

    if not skip_apple:
        apple_client = AppleMusicClient(country=apple_country)

    performances = load_performances(positions, min_year=min_year)
    if not performances:
        console.print("[yellow]No performances found for the given criteria[/yellow]")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"wind": [], "brass": []}, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0

    finder = StreamingLinkFinder(spotify=spotify_client, apple_music=apple_client)

    matches: List[StreamingMatch] = []
    for performance in track(performances, description="Matching streaming links"):
        matches.append(
            StreamingMatch(
                performance=performance,
                spotify=finder.match_spotify(performance) if spotify_client else None,
                apple_music=finder.match_apple(performance) if apple_client else None,
            )
        )

    serialised = [match.to_dict() for match in matches if match.spotify or match.apple_music]

    payload = {
        "wind": serialised,
        "brass": [],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    console.print(f"[green]Wrote {len(serialised)} streaming entries to {output}[/green]")
    return len(serialised)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch streaming links for NM Janitsjar performances")
    parser.add_argument("--positions", type=Path, required=True, help="Path to band positions dataset (JSON)")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the streaming links JSON")
    parser.add_argument("--min-year", type=int, default=2017, help="First year to include (default: 2017)")
    parser.add_argument("--spotify-client-id", type=str, default=os.getenv("SPOTIFY_CLIENT_ID"))
    parser.add_argument("--spotify-client-secret", type=str, default=os.getenv("SPOTIFY_CLIENT_SECRET"))
    parser.add_argument("--apple-country", type=str, default="us", help="Apple Music store country code (default: us)")
    parser.add_argument("--skip-spotify", action="store_true", help="Skip Spotify lookup")
    parser.add_argument("--skip-apple", action="store_true", help="Skip Apple Music lookup")

    args = parser.parse_args()

    generate_streaming_links(
        positions=args.positions,
        output=args.output,
        min_year=args.min_year,
        spotify_client_id=args.spotify_client_id,
        spotify_client_secret=args.spotify_client_secret,
        apple_country=args.apple_country,
        skip_spotify=args.skip_spotify,
        skip_apple=args.skip_apple,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
