"""
URL discovery for Norwegian Wind Band Orchestra competition results.

This module discovers and manages URLs for all yearly competition results
from 1981 to 2025.
"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

console = Console()


class URLDiscovery:
    """Discovers and manages URLs for yearly competition results."""
    
    BASE_URL = "https://www.nmjanitsjar.no"
    RESULTATER_MENU_PATTERN = r"/\d{4}/\d{2}/resultater-(\d{4})\.html"
    
    def __init__(self, cache_file: Path = None):
        """Initialize URL discovery with optional cache file."""
        self.cache_file = cache_file or Path("meta/yearly_urls.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.urls_cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, any]:
        """Load cached URLs from JSON file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Warning: Could not load cache file: {e}[/yellow]")
        
        return {
            "last_updated": None,
            "discovered_urls": {},
            "missing_years": [],
            "metadata": {
                "source": "Auto-discovered from nmjanitsjar.no",
                "pattern": self.RESULTATER_MENU_PATTERN
            }
        }
    
    def _save_cache(self) -> None:
        """Save URLs cache to JSON file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.urls_cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            console.print(f"[red]Error: Could not save cache file: {e}[/red]")
    
    def discover_from_main_page(self) -> Dict[int, str]:
        """
        Discover yearly result URLs by parsing the main site navigation.
        
        Returns:
            Dict mapping year to URL path
        """
        console.print("[blue]Discovering yearly result URLs from main site...[/blue]")
        
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for links in the RESULTATER menu
            resultater_links = soup.find_all('a', href=re.compile(self.RESULTATER_MENU_PATTERN))
            discovered_urls = {}
            
            for link in resultater_links:
                href = link.get('href')
                match = re.search(self.RESULTATER_MENU_PATTERN, href)
                if match:
                    year = int(match.group(1))
                    full_url = urljoin(self.BASE_URL, href)
                    discovered_urls[year] = full_url
            
            console.print(f"[green]Discovered {len(discovered_urls)} yearly result URLs[/green]")
            return discovered_urls
            
        except requests.RequestException as e:
            console.print(f"[red]Error fetching main page: {e}[/red]")
            return {}
    
    def discover_pattern_based(self) -> Dict[int, str]:
        """
        Generate URLs based on known patterns for years 1981-2025.
        
        Note: This is a fallback method that generates URLs based on observed patterns.
        Some URLs may not exist (no competition in certain years).
        """
        console.print("[blue]Generating URLs based on known patterns...[/blue]")
        
        # Known pattern variations (observed from the site)
        patterns = [
            "/2025/04/resultater-{year}.html",
            "/2024/03/resultater-{year}.html", 
            "/2023/03/resultater-{year}.html",
            "/{year}/04/resultater-{year}.html",  # Most common pattern
            "/{year}/03/resultater-{year}.html",  # Alternative pattern
            "/2019/04/resultater-{year}.html",   # Special case for 2019
            "/2019/03/resultater-{year}.html",   # Special case for 2018
            "/2016/03/resultater-{year}.html",   # Special case for older years
            "/2016/02/resultater-{year}.html",   # Special case for 2015
        ]
        
        generated_urls = {}
        
        for year in range(1981, 2026):
            # Try different patterns for each year
            for pattern in patterns:
                url_path = pattern.format(year=year)
                full_url = self.BASE_URL + url_path
                
                # For recent years, use the specific known patterns
                if year >= 2023:
                    if year == 2025:
                        generated_urls[year] = self.BASE_URL + "/2025/04/resultater-2025.html"
                    elif year == 2024:
                        generated_urls[year] = self.BASE_URL + "/2024/03/resultater-2024.html"
                    elif year == 2023:
                        generated_urls[year] = self.BASE_URL + "/2023/03/resultater-2023.html"
                    break
                else:
                    # For older years, use the most common pattern first
                    generated_urls[year] = self.BASE_URL + f"/{year}/04/resultater-{year}.html"
                    break
        
        console.print(f"[yellow]Generated {len(generated_urls)} URLs based on patterns[/yellow]")
        return generated_urls
    
    def verify_urls(self, urls: Dict[int, str]) -> Dict[int, str]:
        """
        Verify that URLs actually exist by making HEAD requests.
        
        Args:
            urls: Dictionary mapping year to URL
            
        Returns:
            Dictionary of verified URLs (only those that exist)
        """
        console.print("[blue]Verifying URL existence...[/blue]")
        
        verified_urls = {}
        missing_years = []
        
        for year, url in track(urls.items(), description="Verifying URLs..."):
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    verified_urls[year] = url
                else:
                    missing_years.append(year)
                    console.print(f"[yellow]Year {year} not found (HTTP {response.status_code}): {url}[/yellow]")
            except requests.RequestException as e:
                missing_years.append(year)
                console.print(f"[red]Year {year} verification failed: {e}[/red]")
        
        # Update cache with verified results
        self.urls_cache["discovered_urls"] = {str(k): v for k, v in verified_urls.items()}
        self.urls_cache["missing_years"] = missing_years
        self.urls_cache["last_updated"] = datetime.now().isoformat()
        
        console.print(f"[green]Verified {len(verified_urls)} existing URLs[/green]")
        console.print(f"[yellow]{len(missing_years)} years not found: {missing_years}[/yellow]")
        
        return verified_urls
    
    def get_all_urls(self, force_refresh: bool = False) -> Dict[int, str]:
        """
        Get all yearly result URLs, using cache if available.
        
        Args:
            force_refresh: If True, bypass cache and rediscover URLs
            
        Returns:
            Dictionary mapping year to URL
        """
        if not force_refresh and self.urls_cache.get("discovered_urls"):
            console.print("[green]Using cached URLs[/green]")
            return {int(k): v for k, v in self.urls_cache["discovered_urls"].items()}
        
        # Try discovering from main page first
        discovered_urls = self.discover_from_main_page()
        
        # If discovery failed or incomplete, use pattern-based approach
        if len(discovered_urls) < 20:  # Expect at least 20 years of data
            console.print("[yellow]Main page discovery incomplete, using pattern-based approach[/yellow]")
            pattern_urls = self.discover_pattern_based()
            discovered_urls.update(pattern_urls)
        
        # Verify URLs actually exist
        verified_urls = self.verify_urls(discovered_urls)
        
        # Save to cache
        self._save_cache()
        
        return verified_urls
    
    def get_url_for_year(self, year: int) -> Optional[str]:
        """Get URL for a specific year."""
        urls = self.get_all_urls()
        return urls.get(year)
    
    def get_missing_years(self) -> List[int]:
        """Get list of years that don't have competition results."""
        self.get_all_urls()  # Ensure cache is populated
        return self.urls_cache.get("missing_years", [])
    
    def get_available_years(self) -> List[int]:
        """Get list of years that have competition results available."""
        urls = self.get_all_urls()
        return sorted(urls.keys())


def main():
    """CLI entry point for URL discovery."""
    discovery = URLDiscovery()
    
    console.print("[bold]Norwegian Wind Band Orchestra URL Discovery[/bold]")
    console.print()
    
    urls = discovery.get_all_urls(force_refresh=True)
    
    console.print(f"\n[bold green]Summary:[/bold green]")
    console.print(f"Available years: {len(urls)}")
    console.print(f"Year range: {min(urls.keys())}-{max(urls.keys())}")
    console.print(f"Missing years: {discovery.get_missing_years()}")
    
    console.print(f"\n[bold]Cache saved to:[/bold] {discovery.cache_file}")


if __name__ == "__main__":
    main()
