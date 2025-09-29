"""
XML parser for Norwegian Brass Band competition results.

This module parses XML data from the nmbrass.no website to extract
structured competition results for brass bands.
"""

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from rich.console import Console
from rich.progress import track

from .models import CompetitionYear, Division, Placement, Award

console = Console()


class BrassXMLParser:
    """Parses XML data from nmbrass.no to extract brass band competition results."""
    
    BASE_URL = "https://nmbrass.no"
    XML_ENDPOINTS = {
        "konkurranser": f"{BASE_URL}/konkurranser.xml",
        "korps": f"{BASE_URL}/korps.xml",
        "dirigenter": f"{BASE_URL}/dirigenter.xml",
        "repertoar": f"{BASE_URL}/repertoar.xml",
    }
    
    def __init__(self, cache_dir: Path = None):
        """
        Initialize XML parser for brass band data.
        
        Args:
            cache_dir: Directory to cache XML data files
        """
        self.cache_dir = cache_dir or Path("data/brass/xml")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Data caches
        self._konkurranser = None
        self._korps = None
        self._dirigenter = None
        self._repertoar = None
        
        # Lookup indexes populated after data load
        self._korps_index: Dict[int, Dict[str, str]] = {}
        self._dirigenter_index: Dict[int, Dict[str, str]] = {}
        self._repertoar_index: Dict[int, Dict[str, str]] = {}
    
    def _fetch_and_cache_xml(self, endpoint_name: str, force_refresh: bool = False) -> ET.Element:
        """
        Fetch XML data from endpoint and cache it locally.
        
        Args:
            endpoint_name: Name of endpoint (konkurranser, korps, etc.)
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            Parsed XML root element
        """
        cache_file = self.cache_dir / f"{endpoint_name}.xml"
        
        # Check cache first
        if not force_refresh and cache_file.exists():
            try:
                console.print(f"[green]Using cached XML for {endpoint_name}[/green]")
                
                # Read raw bytes first
                with open(cache_file, 'rb') as f:
                    raw_content = f.read()
                
                # Detect encoding from XML declaration
                header = raw_content[:200].decode('ascii', errors='ignore')
                declared_encoding = 'utf-8'  # default
                if 'encoding=' in header:
                    import re
                    match = re.search(r'encoding=["\']([^"\']+)["\']', header)
                    if match:
                        declared_encoding = match.group(1)
                
                # Decode using declared encoding
                try:
                    content = raw_content.decode(declared_encoding)
                except (UnicodeDecodeError, LookupError):
                    # Fallback to windows-1252
                    try:
                        content = raw_content.decode('windows-1252')
                    except UnicodeDecodeError:
                        content = raw_content.decode('utf-8', errors='replace')
                
                return ET.fromstring(content)
                
            except ET.ParseError as e:
                console.print(f"[yellow]Could not parse cached {endpoint_name}: {e}, re-downloading[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Cache read failed for {endpoint_name}: {e}[/yellow]")
        
        
        # Fetch from website
        url = self.XML_ENDPOINTS[endpoint_name]
        console.print(f"[blue]Fetching {endpoint_name} from {url}[/blue]")
        
        try:
            # Rate limiting
            time.sleep(1.0)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # XML often declares encoding - try to detect it from the content
            # First, check for <?xml encoding="..."?> declaration
            raw_content = response.content
            
            # Try to find encoding declaration in first 200 bytes
            header = raw_content[:200].decode('ascii', errors='ignore')
            declared_encoding = None
            if 'encoding=' in header:
                import re
                match = re.search(r'encoding=["\']([^"\']+)["\']', header)
                if match:
                    declared_encoding = match.group(1)
            
            # Use declared encoding, fallback to response encoding, then utf-8
            encoding = declared_encoding or response.encoding or 'utf-8'
            
            try:
                content = raw_content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # Fallback to windows-1252 which is common for Norwegian content
                try:
                    content = raw_content.decode('windows-1252')
                except UnicodeDecodeError:
                    content = raw_content.decode('utf-8', errors='replace')
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Cache the raw bytes to preserve original encoding
            try:
                with open(cache_file, 'wb') as f:
                    f.write(raw_content)
                console.print(f"[green]✓ Cached {endpoint_name} XML[/green]")
            except IOError as e:
                console.print(f"[yellow]Warning: Could not cache {endpoint_name}: {e}[/yellow]")
            
            return root
            
        except Exception as e:
            console.print(f"[red]Failed to fetch {endpoint_name}: {e}[/red]")
            raise
    
    def load_all_data(self, force_refresh: bool = False) -> None:
        """
        Load all XML data sources.
        
        Args:
            force_refresh: If True, bypass cache and re-download all data
        """
        console.print("[bold]Loading brass band competition data from XML[/bold]")
        
        self._konkurranser = self._fetch_and_cache_xml("konkurranser", force_refresh)
        self._korps = self._fetch_and_cache_xml("korps", force_refresh)
        self._dirigenter = self._fetch_and_cache_xml("dirigenter", force_refresh)
        self._repertoar = self._fetch_and_cache_xml("repertoar", force_refresh)
        
        # Build fast lookup indexes
        self._korps_index = {}
        for korps in self._korps.findall(".//korps"):
            korpsnr_elem = korps.find("korpsnr")
            korpsnavn_elem = korps.find("korpsnavn")
            bildelink_elem = korps.find("bildelink")
            
            if korpsnr_elem is not None and korpsnr_elem.text:
                korpsnr = int(korpsnr_elem.text.strip())
                self._korps_index[korpsnr] = {
                    "korpsnavn": korpsnavn_elem.text.strip() if korpsnavn_elem is not None and korpsnavn_elem.text else "Unknown",
                    "bildelink": bildelink_elem.text.strip() if bildelink_elem is not None and bildelink_elem.text and bildelink_elem.text != "-" else None
                }
        
        self._dirigenter_index = {}
        for dirigent in self._dirigenter.findall(".//dirigent"):
            dirigentnr_elem = dirigent.find("dirigentnr")
            dirigentnavn_elem = dirigent.find("dirigentnavn")
            
            if dirigentnr_elem is not None and dirigentnr_elem.text:
                dirigentnr = int(dirigentnr_elem.text.strip())
                self._dirigenter_index[dirigentnr] = {
                    "dirigentnavn": dirigentnavn_elem.text.strip() if dirigentnavn_elem is not None and dirigentnavn_elem.text else "Unknown"
                }
        
        self._repertoar_index = {}
        for stykke in self._repertoar.findall(".//musikkstykke"):
            repertoarnr_elem = stykke.find("repertoarnr")
            tittel_elem = stykke.find("tittel")
            komponist_elem = stykke.find("komponist")
            
            if repertoarnr_elem is not None and repertoarnr_elem.text:
                repertoarnr = int(repertoarnr_elem.text.strip())
                self._repertoar_index[repertoarnr] = {
                    "tittel": tittel_elem.text.strip() if tittel_elem is not None and tittel_elem.text else "Unknown",
                    "komponist": komponist_elem.text.strip() if komponist_elem is not None and komponist_elem.text else ""
                }
        
        console.print("[green]✓ All brass band data loaded successfully[/green]")
        console.print(f"  • {len(self._korps_index)} orchestras")
        console.print(f"  • {len(self._dirigenter_index)} conductors")
        console.print(f"  • {len(self._repertoar_index)} repertoire pieces")
    
    def _normalize_identifier(self, value: Any) -> Optional[int]:
        """Return a clean integer identifier or None when not available."""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.strip()
            if value in {"", "-", "--"}:
                return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    
    def _normalize_rank(self, value: Any) -> Optional[int]:
        """Return a valid rank integer or None when unavailable."""
        return self._normalize_identifier(value)
    
    def _normalize_points(self, value: Any) -> Optional[float]:
        """Return numeric points; treat dashes and malformed strings as missing."""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.strip()
            if value in {"", "-", "--"}:
                return None
            value = value.replace(",", ".")
            try:
                return float(value)
            except ValueError:
                console.print(f"[yellow]Warning: could not parse points value '{value}' as float[/yellow]")
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    def _parse_placement(self, resultat: ET.Element, year: int) -> Optional[Placement]:
        """Parse a single competition placement from XML element."""
        try:
            # Extract basic data
            aarstall_elem = resultat.find("aarstall")
            divisjon_elem = resultat.find("divisjon")
            plassering_elem = resultat.find("plassering")
            korpsnr_elem = resultat.find("korpsnr")
            dirigentnr_elem = resultat.find("dirigentnr")
            repertoarnr_elem = resultat.find("repertoarnr")
            poengtotalt_elem = resultat.find("poengtotalt")
            
            # Validate year matches
            if aarstall_elem is not None and aarstall_elem.text:
                resultat_year = int(aarstall_elem.text.strip())
                if resultat_year != year:
                    return None  # Skip results from other years
            
            rank = self._normalize_rank(plassering_elem.text if plassering_elem is not None else None)
            points = self._normalize_points(poengtotalt_elem.text if poengtotalt_elem is not None else None)
            korpsnr = self._normalize_identifier(korpsnr_elem.text if korpsnr_elem is not None else None)
            dirigentnr = self._normalize_identifier(dirigentnr_elem.text if dirigentnr_elem is not None else None)
            repertoarnr = self._normalize_identifier(repertoarnr_elem.text if repertoarnr_elem is not None else None)
            
            # Get orchestra info
            orchestra_name = "Unknown Orchestra"
            image_url = None
            if korpsnr is not None and korpsnr in self._korps_index:
                orchestra_name = self._korps_index[korpsnr]["korpsnavn"]
                image_url = self._korps_index[korpsnr].get("bildelink")
            elif korpsnr is not None:
                orchestra_name = f"Unknown Orchestra #{korpsnr}"
            
            # Get conductor info
            conductor_name = "Ukjent"
            if dirigentnr is not None and dirigentnr in self._dirigenter_index:
                conductor_name = self._dirigenter_index[dirigentnr]["dirigentnavn"]
            
            # Get musical piece info
            pieces: List[str] = []
            if repertoarnr is not None and repertoarnr in self._repertoar_index:
                piece_info = self._repertoar_index[repertoarnr]
                title = piece_info["tittel"]
                composer = piece_info["komponist"]
                
                if title and composer:
                    pieces.append(f"{title} – {composer}")
                elif title:
                    pieces.append(title)
            
            return Placement(
                rank=rank,
                orchestra=orchestra_name,
                pieces=pieces,
                points=points,
                conductor=conductor_name,
                orchestra_url=None,
                conductor_url=None,
                piece_urls=[],
                image_url=image_url
            )
            
        except Exception as e:
            console.print(f"[red]Error parsing placement: {e}[/red]")
            return None
    
    def _division_sort_key(self, division: Division) -> tuple:
        """Generate sort key for divisions (Elite first, then numerical order)."""
        import re
        name = division.name.lower()
        
        if "elite" in name:
            return (0, 0)
        elif "divisjon" in name or any(char.isdigit() for char in name):
            # Extract number from division name
            match = re.search(r'(\d+)', name)
            if match:
                return (1, int(match.group(1)))
        
        # Unknown division types go last
        return (999, 0)
    
    def parse_year(self, year: int) -> CompetitionYear:
        """
        Parse competition results for a specific year.
        
        Args:
            year: Competition year to parse
            
        Returns:
            CompetitionYear object with all divisions and placements
        """
        if self._konkurranser is None:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        console.print(f"[blue]Parsing brass band competition data for {year}[/blue]")
        
        # Filter results for the specific year
        year_results = []
        for resultat in self._konkurranser.findall(".//resultat"):
            aarstall_elem = resultat.find("aarstall")
            if aarstall_elem is not None and aarstall_elem.text:
                if int(aarstall_elem.text.strip()) == year:
                    year_results.append(resultat)
        
        if not year_results:
            console.print(f"[yellow]No competitions found for year {year}[/yellow]")
            return CompetitionYear(year=year, divisions=[])
        
        # Group by division
        divisions_data: Dict[str, List[ET.Element]] = {}
        for resultat in year_results:
            divisjon_elem = resultat.find("divisjon")
            divisjon = "Unknown"
            if divisjon_elem is not None and divisjon_elem.text:
                divisjon = divisjon_elem.text.strip()
                # Normalize division names
                if divisjon.isdigit():
                    divisjon = f"{divisjon}. divisjon"
            
            if divisjon not in divisions_data:
                divisions_data[divisjon] = []
            divisions_data[divisjon].append(resultat)
        
        # Parse each division
        divisions = []
        for divisjon_name, results in divisions_data.items():
            # Sort by placement
            def placement_key(res: ET.Element) -> int:
                plassering_elem = res.find("plassering")
                if plassering_elem is not None and plassering_elem.text:
                    normalized = self._normalize_rank(plassering_elem.text)
                    return normalized if normalized is not None else 999
                return 999
            
            results.sort(key=placement_key)
            
            placements = []
            for resultat in results:
                placement = self._parse_placement(resultat, year)
                if placement:
                    placements.append(placement)
            
            # Create division
            division = Division(
                name=divisjon_name,
                placements=placements,
                awards=[]  # Awards might not be in XML
            )
            divisions.append(division)
        
        # Sort divisions (Elite first, then 1., 2., etc.)
        divisions.sort(key=self._division_sort_key)
        
        competition_year = CompetitionYear(
            year=year,
            divisions=divisions,
            total_orchestras=len(year_results)
        )
        
        console.print(f"[green]✓ Parsed {len(divisions)} divisions with {len(year_results)} total placements[/green]")
        return competition_year
    
    def get_available_years(self) -> List[int]:
        """Get list of years that have competition data."""
        if self._konkurranser is None:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        years = set()
        for resultat in self._konkurranser.findall(".//resultat"):
            aarstall_elem = resultat.find("aarstall")
            if aarstall_elem is not None and aarstall_elem.text:
                years.add(int(aarstall_elem.text.strip()))
        
        return sorted(years)
    
    def get_divisions_for_year(self, year: int) -> List[str]:
        """Get list of division names for a specific year."""
        if self._konkurranser is None:
            raise RuntimeError("Data not loaded. Call load_all_data() first.")
        
        divisions = set()
        for resultat in self._konkurranser.findall(".//resultat"):
            aarstall_elem = resultat.find("aarstall")
            divisjon_elem = resultat.find("divisjon")
            
            if (aarstall_elem is not None and aarstall_elem.text and 
                int(aarstall_elem.text.strip()) == year and
                divisjon_elem is not None and divisjon_elem.text):
                divisjon = divisjon_elem.text.strip()
                if divisjon.isdigit():
                    divisjon = f"{divisjon}. divisjon"
                divisions.add(divisjon)
        
        return sorted(divisions, key=lambda d: self._division_sort_key(Division(name=d, placements=[], awards=[])))


def main():
    """CLI entry point for brass band XML parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse Norwegian Brass Band competition data")
    parser.add_argument("--year", type=int, help="Specific year to parse")
    parser.add_argument("--all-years", action="store_true", help="Show all available years")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached XML data")
    
    args = parser.parse_args()
    
    brass_parser = BrassXMLParser()
    brass_parser.load_all_data(args.force_refresh)
    
    if args.all_years:
        available_years = brass_parser.get_available_years()
        console.print(f"[bold]Available years:[/bold] {available_years}")
        console.print(f"Total years: {len(available_years)}")
        if available_years:
            console.print(f"Year range: {min(available_years)}-{max(available_years)}")
        return
    
    if args.year:
        competition_year = brass_parser.parse_year(args.year)
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