"""
JSON parser for Norwegian Wind Band Orchestra competition results.

This module parses JSON data from the nmjanitsjar.no API to extract
structured competition results.
"""

import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

import requests
from rich.console import Console

from .models import CompetitionYear, Division, Placement, Award

console = Console()


class JSONParser:
    """Parses JSON data from nmjanitsjar.no to extract competition results."""
    
    JSON_BASE_URL = "https://nmbrass.no/nmjanitsjar"
    JSON_ENDPOINTS = {
        "konkurranser": f"{JSON_BASE_URL}/konkurranser.json",
        "korps": f"{JSON_BASE_URL}/korps.json", 
        "dirigenter": f"{JSON_BASE_URL}/dirigenter.json",
        "musikkstykker": f"{JSON_BASE_URL}/musikkstykker.json",
        "repmus": f"{JSON_BASE_URL}/repmus.json"
    }
    
    KNOWLEDGE_FILE = Path("meta/manual_overrides.json")

    def __init__(self, cache_dir: Path = None):
        """
        Initialize JSON parser.
        
        Args:
            cache_dir: Directory to cache JSON data files
        """
        self.cache_dir = cache_dir or Path("data/json")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data caches
        self._konkurranser = None
        self._korps = None
        self._dirigenter = None
        self._musikkstykker = None
        self._repmus = None

        # Lookup indexes populated after data load
        self._korps_index: Dict[int, Dict[str, Any]] = {}
        self._dirigenter_index: Dict[int, Dict[str, Any]] = {}
        self._musikkstykker_index: Dict[int, Dict[str, Any]] = {}
        self._repertoar_index: Dict[int, List[Dict[str, Any]]] = {}

        # Local knowledge overrides
        self.manual_overrides: Dict[str, Dict[str, str]] = self._load_manual_overrides()
        
    def _clean_json_content(self, raw_content: str) -> str:
        """
        Clean JSON content by removing JavaScript variable declaration.
        
        The JSON files contain JavaScript like 'var JSONname = {...}'
        We need to extract just the {...} part.
        """
        # Find the JSON object part
        start_idx = raw_content.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in content")
        
        # Find the matching closing brace
        brace_count = 0
        for i in range(start_idx, len(raw_content)):
            if raw_content[i] == '{':
                brace_count += 1
            elif raw_content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return raw_content[start_idx:i+1]
        
        raise ValueError("Could not find complete JSON object")
    
    def _fetch_and_cache_json(self, endpoint_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch JSON data from endpoint and cache it locally.
        
        Args:
            endpoint_name: Name of endpoint (konkurranser, korps, etc.)
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            Parsed JSON data
        """
        cache_file = self.cache_dir / f"{endpoint_name}.json"
        
        # Check cache first
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Cache read failed for {endpoint_name}: {e}[/yellow]")
        
        # Fetch from API
        url = self.JSON_ENDPOINTS[endpoint_name]
        console.print(f"[blue]Fetching {endpoint_name} from {url}[/blue]")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Clean and parse JSON
            cleaned_json = self._clean_json_content(response.text)
            data = json.loads(cleaned_json)
            
            # Cache the cleaned data
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                console.print(f"[green]✓ Cached {endpoint_name} JSON[/green]")
            except IOError as e:
                console.print(f"[yellow]Warning: Could not cache {endpoint_name}: {e}[/yellow]")
            
            return data
            
        except Exception as e:
            console.print(f"[red]Failed to fetch {endpoint_name}: {e}[/red]")
            raise
    
    def load_all_data(self, force_refresh: bool = False) -> None:
        """
        Load all JSON data sources.
        
        Args:
            force_refresh: If True, bypass cache and re-download all data
        """
        console.print("[bold]Loading competition data from JSON APIs[/bold]")
        
        self._konkurranser = self._fetch_and_cache_json("konkurranser", force_refresh)
        self._korps = self._fetch_and_cache_json("korps", force_refresh)
        self._dirigenter = self._fetch_and_cache_json("dirigenter", force_refresh)
        self._musikkstykker = self._fetch_and_cache_json("musikkstykker", force_refresh)

        # repmus is optional
        try:
            self._repmus = self._fetch_and_cache_json("repmus", force_refresh)
        except Exception:
            console.print("[yellow]Could not load repmus data (non-critical)[/yellow]")
            self._repmus = {"repmus": []}

        # Build fast lookup indexes
        self._korps_index = {
            int(korps["korpsnr"]): korps
            for korps in self._korps.get("korps", [])
            if korps.get("korpsnr") is not None
        }
        self._dirigenter_index = {
            int(dirigent["dirigentnr"]): dirigent
            for dirigent in self._dirigenter.get("dirigenter", [])
            if dirigent.get("dirigentnr") is not None
        }
        self._musikkstykker_index = {
            int(stykke["musikkstykkenr"]): stykke
            for stykke in self._musikkstykker.get("musikkstykker", [])
            if stykke.get("musikkstykkenr") is not None
        }

        repertoar_index: Dict[int, List[Dict[str, Any]]] = {}
        for rep in self._repmus.get("repmus", []):
            repertoarnr = rep.get("repertoarnr")
            if repertoarnr is None:
                continue
            key = int(repertoarnr)
            repertoar_index.setdefault(key, []).append(rep)
        self._repertoar_index = repertoar_index

        console.print("[green]✓ All data loaded successfully[/green]")

    def _load_manual_overrides(self) -> Dict[str, Dict[str, str]]:
        """Load optional manual overrides for known data gaps."""
        default: Dict[str, Dict[str, str]] = {"conductors": {}}
        path = self.KNOWLEDGE_FILE
        if not path.exists():
            return default

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            console.print(
                f"[yellow]Warning: failed to load manual overrides from {path}: {exc}[/yellow]"
            )
            return default

        # Ensure expected structure even if file is missing specific sections.
        if "conductors" not in data or not isinstance(data["conductors"], dict):
            data["conductors"] = {}

        return data

    def _get_manual_conductor(self, year: Optional[int], korpsnr: Optional[int]) -> Optional[str]:
        """Lookup a manually specified conductor override."""
        if year is None or korpsnr is None:
            return None
        key = f"{int(year)}:{int(korpsnr)}"
        return self.manual_overrides.get("conductors", {}).get(key)

    def _normalize_identifier(self, identifier: Any) -> Optional[int]:
        """Return a clean integer identifier or None when not available."""
        if identifier is None:
            return None
        if isinstance(identifier, str):
            candidate = identifier.strip()
            if candidate in {"", "-", "--"}:
                return None
        try:
            return int(identifier)
        except (TypeError, ValueError):
            return None

    def _normalize_rank(self, rank: Any) -> Optional[int]:
        """Return a valid rank integer or None when unavailable."""
        if isinstance(rank, (int, float)) and not isinstance(rank, bool):
            return int(rank)
        if isinstance(rank, str):
            candidate = rank.strip()
            if candidate in {"", "-", "--"}:
                return None
            try:
                return int(candidate)
            except ValueError:
                return None
        return None

    def _normalize_points(self, value: Any) -> Optional[float]:
        """Return numeric points; treat dashes and malformed strings as missing."""
        if value is None:
            return None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        if isinstance(value, str):
            candidate = value.strip()
            if candidate in {"", "-", "--"}:
                return None

            # Some records append suffixes like "-1" or use commas as decimal separators.
            parts = candidate.split("-")
            if parts:
                candidate = parts[0]
            candidate = candidate.replace(",", ".").strip()
            # Remove any stray percent or whitespace characters.
            candidate = candidate.rstrip("%")

            try:
                return float(candidate)
            except ValueError:
                console.print(
                    f"[yellow]Warning: could not parse points value '{value}' as float; treating as missing[/yellow]"
                )
                return None
        return None

    def _get_korps_by_nr(self, korpsnr: int) -> Optional[Dict[str, Any]]:
        """Get orchestra info by korpsnr."""
        return self._korps_index.get(int(korpsnr)) if korpsnr is not None else None

    def _get_dirigent_by_nr(self, dirigentnr: int) -> Optional[Dict[str, Any]]:
        """Get conductor info by dirigentnr."""
        return self._dirigenter_index.get(int(dirigentnr)) if dirigentnr is not None else None

    def _get_musikkstykke_by_nr(self, musikkstykkenr: int) -> Optional[Dict[str, Any]]:
        """Get musical piece info by musikkstykkenr."""
        return self._musikkstykker_index.get(int(musikkstykkenr)) if musikkstykkenr is not None else None

    def _get_repertoar_for_repertoarnr(self, repertoarnr: Optional[int]) -> List[Dict[str, Any]]:
        """Get all repertoire entries attached to a specific repertoire id."""
        if repertoarnr is None:
            return []
        return self._repertoar_index.get(int(repertoarnr), [])
    
    def parse_year(self, year: int) -> CompetitionYear:
        """
        Parse competition results for a specific year.
        
        Args:
            year: Competition year to parse
            
        Returns:
            CompetitionYear object with all divisions and placements
        """
        if not self._konkurranser:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        console.print(f"[blue]Parsing competition data for {year}[/blue]")
        
        # Filter competitions for the specific year
        year_competitions = [
            comp for comp in self._konkurranser.get("konkurranser", [])
            if comp.get("aarstall") == year
        ]
        
        if not year_competitions:
            console.print(f"[yellow]No competitions found for year {year}[/yellow]")
            return CompetitionYear(year=year, divisions=[])
        
        # Group by division
        divisions_data = {}
        for comp in year_competitions:
            divisjon = comp.get("divisjon", "Unknown")
            # Convert numeric divisions to string format
            if isinstance(divisjon, int):
                divisjon = f"{divisjon}. divisjon"
            elif isinstance(divisjon, str) and divisjon.isdigit():
                divisjon = f"{divisjon}. divisjon"
            
            if divisjon not in divisions_data:
                divisions_data[divisjon] = []
            divisions_data[divisjon].append(comp)
        
        # Parse each division
        divisions = []
        for divisjon_name, comps in divisions_data.items():
            # Sort by placement, allowing unknown ranks to fall to the end
            def placement_key(comp: Dict[str, Any]) -> int:
                normalized = self._normalize_rank(comp.get("plassering"))
                return normalized if normalized is not None else 999

            comps.sort(key=placement_key)
            
            placements = []
            for comp in comps:
                placement = self._parse_placement(comp)
                if placement:
                    placements.append(placement)
            
            # Create division
            division = Division(
                name=divisjon_name,
                placements=placements,
                awards=[]  # Awards are not in the JSON structure we found
            )
            divisions.append(division)
        
        # Sort divisions (Elite first, then 1., 2., etc.)
        divisions.sort(key=self._division_sort_key)
        
        competition_year = CompetitionYear(
            year=year,
            divisions=divisions,
            total_orchestras=len(year_competitions)
        )
        
        console.print(f"[green]✓ Parsed {len(divisions)} divisions with {len(year_competitions)} total placements[/green]")
        return competition_year
    
    def _parse_placement(self, comp_data: Dict[str, Any]) -> Optional[Placement]:
        """Parse a single competition placement from JSON data."""
        try:
            # Get basic data
            rank = self._normalize_rank(comp_data.get("plassering"))
            points = self._normalize_points(comp_data.get("poengtotalt"))
            korpsnr = comp_data.get("korpsnr")
            dirigentnr = self._normalize_identifier(comp_data.get("dirigentnr"))
            repertoarnr = self._normalize_identifier(comp_data.get("repertoarnr"))

            # Get orchestra info
            korps_info = self._get_korps_by_nr(korpsnr) if korpsnr else None
            orchestra_name = korps_info.get("korpsnavn", f"Unknown Orchestra #{korpsnr}") if korps_info else f"Unknown Orchestra #{korpsnr}"
            image_url = korps_info.get("bildelink") if korps_info and korps_info.get("bildelink") != "-" else None

            # Get conductor info
            dirigent_info = self._get_dirigent_by_nr(dirigentnr) if dirigentnr else None
            conductor_name = dirigent_info.get("dirigentnavn") if dirigent_info else None

            manual_conductor = self._get_manual_conductor(comp_data.get("aarstall"), korpsnr)
            if manual_conductor:
                conductor_name = manual_conductor

            if not conductor_name:
                conductor_name = "Ukjent"
            
            # Get musical piece info
            pieces: List[str] = []
            if repertoarnr is not None:
                repertoire_entries = self._get_repertoar_for_repertoarnr(repertoarnr)
                for rep_entry in repertoire_entries:
                    musikkstykkenr = self._normalize_identifier(rep_entry.get("musikkstykkenr"))
                    musikkstykke = self._get_musikkstykke_by_nr(musikkstykkenr) if musikkstykkenr else None
                    title = musikkstykke.get("tittel") if musikkstykke else None
                    if not title:
                        continue

                    label = title.strip()
                    if not label:
                        continue

                    plikt = str(rep_entry.get("plikt", "")).strip().upper()
                    if plikt == "P":
                        label = f"{label} (plikt)"

                    pieces.append(label)

                # Some historical entries only provide a direct musikkstykkenr
                if not pieces:
                    musikkstykke = self._get_musikkstykke_by_nr(repertoarnr)
                    if musikkstykke and musikkstykke.get("tittel"):
                        pieces.append(str(musikkstykke["tittel"]).strip())

            return Placement(
                rank=rank,
                orchestra=orchestra_name,
                pieces=pieces,
                points=points,
                conductor=conductor_name,
                orchestra_url=None,  # Not available in JSON
                conductor_url=None,  # Not available in JSON
                piece_urls=[],      # Not available in JSON
                image_url=image_url
            )
            
        except Exception as e:
            console.print(f"[red]Error parsing placement: {e}[/red]")
            return None
    
    def _division_sort_key(self, division: Division) -> tuple:
        """Generate sort key for divisions (Elite first, then numerical order)."""
        name = division.name.lower()
        
        if "elite" in name:
            return (0, 0)
        elif "divisjon" in name or "div" in name:
            # Extract number from division name
            match = re.search(r'(\d+)', name)
            if match:
                return (1, int(match.group(1)))
        
        # Unknown division types go last
        return (999, 0)
    
    def get_available_years(self) -> List[int]:
        """Get list of years that have competition data."""
        if not self._konkurranser:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        years = set()
        for comp in self._konkurranser.get("konkurranser", []):
            aarstall = comp.get("aarstall")
            if aarstall:
                years.add(aarstall)
        
        return sorted(years)
    
    def get_divisions_for_year(self, year: int) -> List[str]:
        """Get list of division names for a specific year."""
        if not self._konkurranser:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        divisions = set()
        for comp in self._konkurranser.get("konkurranser", []):
            if comp.get("aarstall") == year:
                divisjon = comp.get("divisjon")
                if divisjon:
                    # Convert numeric divisions to string format
                    if isinstance(divisjon, int):
                        divisjon = f"{divisjon}. divisjon"
                    elif isinstance(divisjon, str) and divisjon.isdigit():
                        divisjon = f"{divisjon}. divisjon"
                    divisions.add(divisjon)
        
        return sorted(divisions, key=lambda d: self._division_sort_key(Division(name=d, placements=[], awards=[])))


def main():
    """CLI entry point for JSON parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse Norwegian Wind Band Orchestra competition data")
    parser.add_argument("--year", type=int, help="Specific year to parse")
    parser.add_argument("--all-years", action="store_true", help="Show all available years")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached JSON data")
    
    args = parser.parse_args()
    
    json_parser = JSONParser()
    json_parser.load_all_data(args.force_refresh)
    
    if args.all_years:
        available_years = json_parser.get_available_years()
        console.print(f"[bold]Available years:[/bold] {available_years}")
        console.print(f"Total years: {len(available_years)}")
        console.print(f"Year range: {min(available_years)}-{max(available_years)}")
        return
    
    if args.year:
        competition_year = json_parser.parse_year(args.year)
        console.print(f"[bold]Competition {args.year}:[/bold]")
        console.print(f"Total orchestras: {competition_year.total_orchestras}")
        console.print(f"Divisions: {len(competition_year.divisions)}")
        
        for division in competition_year.divisions:
            console.print(f"  {division.name}: {len(division.placements)} orchestras")
    else:
        console.print("[red]Please specify --year or --all-years[/red]")
        parser.print_help()


if __name__ == "__main__":
    main()
