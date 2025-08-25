"""
HTML fetcher for Norwegian Wind Band Orchestra competition results.

This module handles downloading and caching of yearly result pages with
resilient retry logic and respectful rate limiting.
"""

import time
from pathlib import Path
from typing import Optional, Dict, List
from urllib.robotparser import RobotFileParser

import requests
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .url_discovery import URLDiscovery

console = Console()


class HTMLFetcher:
    """Downloads and caches HTML content from yearly result pages."""
    
    def __init__(self, cache_dir: Path = None, rate_limit: float = 1.0):
        """
        Initialize HTML fetcher.
        
        Args:
            cache_dir: Directory to store cached HTML files
            rate_limit: Minimum seconds between requests
        """
        self.cache_dir = cache_dir or Path("data/raw")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self.session = self._create_session()
        self.url_discovery = URLDiscovery()
        
        # Check robots.txt
        self._check_robots_txt()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with proper headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': ('nmjanitsjar-scraper/0.1.0 '
                          '(Educational research project for Norwegian wind band data)')
        })
        return session
        
    def _check_robots_txt(self) -> None:
        """Check if we're allowed to scrape according to robots.txt."""
        try:
            rp = RobotFileParser()
            rp.set_url("https://www.nmjanitsjar.no/robots.txt")
            rp.read()
            
            can_fetch = rp.can_fetch('*', 'https://www.nmjanitsjar.no/')
            if not can_fetch:
                console.print("[yellow]Warning: robots.txt suggests we shouldn't scrape this site[/yellow]")
            else:
                console.print("[green]✓ robots.txt allows scraping[/green]")
                
        except Exception as e:
            console.print(f"[yellow]Warning: Could not check robots.txt: {e}[/yellow]")
    
    def _get_cache_path(self, year: int) -> Path:
        """Get cache file path for a given year."""
        return self.cache_dir / f"{year}.html"
    
    def is_cached(self, year: int) -> bool:
        """Check if HTML for a year is already cached."""
        cache_path = self._get_cache_path(year)
        return cache_path.exists() and cache_path.stat().st_size > 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.ConnectionError)),
        before_sleep=before_sleep_log(console.log, log_level="WARNING")
    )
    def _fetch_url(self, url: str) -> str:
        """Fetch HTML content from URL with retry logic."""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    
    def fetch_year(self, year: int, force_refresh: bool = False) -> Optional[str]:
        """
        Fetch HTML content for a specific year.
        
        Args:
            year: Competition year to fetch
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            HTML content as string, or None if failed
        """
        cache_path = self._get_cache_path(year)
        
        # Check cache first
        if not force_refresh and self.is_cached(year):
            console.print(f"[green]Using cached HTML for {year}[/green]")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except IOError as e:
                console.print(f"[yellow]Cache read failed for {year}: {e}[/yellow]")
        
        # Get URL for year
        url = self.url_discovery.get_url_for_year(year)
        if not url:
            console.print(f"[red]No URL found for year {year}[/red]")
            return None
        
        console.print(f"[blue]Fetching {year} from {url}[/blue]")
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit)
            
            # Fetch content
            html_content = self._fetch_url(url)
            
            # Cache the content
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                console.print(f"[green]✓ Cached HTML for {year}[/green]")
            except IOError as e:
                console.print(f"[yellow]Warning: Could not cache {year}: {e}[/yellow]")
            
            return html_content
            
        except Exception as e:
            console.print(f"[red]Failed to fetch {year}: {e}[/red]")
            return None
    
    def fetch_multiple_years(self, years: List[int], force_refresh: bool = False) -> Dict[int, Optional[str]]:
        """
        Fetch HTML content for multiple years with progress tracking.
        
        Args:
            years: List of years to fetch
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            Dictionary mapping year to HTML content (or None if failed)
        """
        console.print(f"[bold]Fetching HTML for {len(years)} years[/bold]")
        
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            
            task = progress.add_task("Downloading pages...", total=len(years))
            
            for year in years:
                progress.update(task, description=f"Fetching year {year}")
                
                html_content = self.fetch_year(year, force_refresh)
                results[year] = html_content
                
                progress.update(task, advance=1)
        
        successful = sum(1 for content in results.values() if content is not None)
        console.print(f"[green]Successfully fetched {successful}/{len(years)} pages[/green]")
        
        return results
    
    def fetch_all_available_years(self, force_refresh: bool = False) -> Dict[int, Optional[str]]:
        """
        Fetch HTML content for all available years.
        
        Args:
            force_refresh: If True, bypass cache and re-download
            
        Returns:
            Dictionary mapping year to HTML content (or None if failed)
        """
        available_years = self.url_discovery.get_available_years()
        console.print(f"[blue]Found {len(available_years)} available years: {min(available_years)}-{max(available_years)}[/blue]")
        
        return self.fetch_multiple_years(available_years, force_refresh)
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get statistics about cached files."""
        cached_files = list(self.cache_dir.glob("*.html"))
        
        stats = {
            "total_cached_files": len(cached_files),
            "cached_years": [],
            "total_size_mb": 0,
            "oldest_cache": None,
            "newest_cache": None
        }
        
        if cached_files:
            # Extract years and calculate sizes
            for file_path in cached_files:
                try:
                    year = int(file_path.stem)
                    stats["cached_years"].append(year)
                    stats["total_size_mb"] += file_path.stat().st_size
                except (ValueError, OSError):
                    continue
            
            # Sort years and convert size to MB
            stats["cached_years"].sort()
            stats["total_size_mb"] = round(stats["total_size_mb"] / (1024 * 1024), 2)
            
            # Get cache date range
            if stats["cached_years"]:
                stats["oldest_cache"] = min(stats["cached_years"])
                stats["newest_cache"] = max(stats["cached_years"])
        
        return stats


def main():
    """CLI entry point for HTML fetching."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch HTML for Norwegian Wind Band Orchestra results")
    parser.add_argument("--years", nargs="+", type=int, help="Specific years to fetch")
    parser.add_argument("--all", action="store_true", help="Fetch all available years")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached files")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    
    args = parser.parse_args()
    
    fetcher = HTMLFetcher()
    
    if args.stats:
        stats = fetcher.get_cache_stats()
        console.print("[bold]Cache Statistics:[/bold]")
        console.print(f"Total cached files: {stats['total_cached_files']}")
        console.print(f"Cached years: {stats['cached_years']}")
        console.print(f"Total size: {stats['total_size_mb']} MB")
        if stats['oldest_cache']:
            console.print(f"Date range: {stats['oldest_cache']}-{stats['newest_cache']}")
        return
    
    if args.all:
        fetcher.fetch_all_available_years(args.force_refresh)
    elif args.years:
        fetcher.fetch_multiple_years(args.years, args.force_refresh)
    else:
        console.print("[red]Please specify --all or --years[/red]")
        parser.print_help()


if __name__ == "__main__":
    main()
