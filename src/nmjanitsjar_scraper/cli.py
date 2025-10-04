"""
Main CLI interface for Norwegian Wind Band Orchestra data scraper.

This module provides a unified command-line interface for all functionality
including URL discovery, data fetching, parsing, exporting, and analytics.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .url_discovery import URLDiscovery
from .fetcher import HTMLFetcher
from .parser import JSONParser
from .exporter import DataExporter
from .analytics import CompetitionAnalytics
from .streaming_search import generate_streaming_links

console = Console()


def show_banner():
    """Display application banner."""
    banner = Text("🎺 Norwegian Wind Band Orchestra Data Scraper 🎺", style="bold magenta")
    console.print(Panel(banner, expand=False))
    console.print()


def run_pipeline(years=None, force_refresh=False):
    """
    Run the complete data pipeline.
    
    Args:
        years: Specific years to process, or None for all
        force_refresh: Force refresh of all cached data
    """
    console.print("[bold]🚀 Running complete data pipeline[/bold]")
    console.print()
    
    try:
        # Step 1: URL Discovery
        console.print("[blue]Step 1: URL Discovery[/blue]")
        url_discovery = URLDiscovery()
        available_urls = url_discovery.get_all_urls(force_refresh)
        console.print(f"✓ Found URLs for {len(available_urls)} years")
        console.print()
        
        # Step 2: Data Fetching (if needed - but we use JSON API instead)
        console.print("[blue]Step 2: Data Loading[/blue]")
        parser = JSONParser()
        parser.load_all_data(force_refresh)
        available_years = parser.get_available_years()
        console.print(f"✓ Loaded data for {len(available_years)} years")
        console.print()
        
        # Step 3: Data Export
        console.print("[blue]Step 3: Data Export[/blue]")
        exporter = DataExporter()
        
        if years:
            # Export specific years
            export_years = [y for y in years if y in available_years]
            if not export_years:
                console.print(f"[red]No data available for years: {years}[/red]")
                return False
            result = exporter.export_all_years(export_years)
        else:
            # Export all years
            result = exporter.export_all_years()
        
        console.print(f"✓ Exported {result['total_placements']} placements across {result['total_years']} years")
        console.print()
        
        # Step 4: Basic Analytics
        console.print("[blue]Step 4: Basic Analytics[/blue]")
        analytics = CompetitionAnalytics()
        stats = analytics.get_summary_stats()
        
        console.print(f"✓ Analysis complete:")
        console.print(f"  • {stats['total_orchestras']} unique orchestras")
        console.print(f"  • {stats['total_conductors']} unique conductors") 
        console.print(f"  • {stats['year_range']} year range")
        console.print(f"  • {stats['avg_points']:.1f} average points")
        console.print()
        
        console.print("[bold green]🎉 Pipeline completed successfully![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Pipeline failed: {e}[/red]")
        return False


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Norwegian Wind Band Orchestra Competition Data Scraper",
        epilog="For detailed help on subcommands, use: nmjanitsjar <command> --help"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run complete data pipeline')
    pipeline_parser.add_argument('--years', nargs='+', type=int, help='Specific years to process')
    pipeline_parser.add_argument('--force-refresh', action='store_true', help='Force refresh all cached data')
    
    # URL discovery command
    url_parser = subparsers.add_parser('urls', help='Discover and manage result URLs')
    url_parser.add_argument('--force-refresh', action='store_true', help='Force refresh URL cache')
    url_parser.add_argument('--show', action='store_true', help='Show discovered URLs')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch HTML pages')
    fetch_parser.add_argument('--years', nargs='+', type=int, help='Specific years to fetch')
    fetch_parser.add_argument('--all', action='store_true', help='Fetch all available years')
    fetch_parser.add_argument('--force-refresh', action='store_true', help='Force refresh cached pages')
    fetch_parser.add_argument('--stats', action='store_true', help='Show fetch statistics')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse competition data')
    parse_parser.add_argument('--year', type=int, help='Parse specific year')
    parse_parser.add_argument('--all-years', action='store_true', help='Show all available years')
    parse_parser.add_argument('--force-refresh', action='store_true', help='Force refresh JSON cache')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV/JSON')
    export_parser.add_argument('--year', type=int, help='Export specific year')
    export_parser.add_argument('--years', nargs='+', type=int, help='Export specific years')
    export_parser.add_argument('--all', action='store_true', help='Export all available years')
    export_parser.add_argument('--stats', action='store_true', help='Show export statistics')
    
    # Analytics command
    stats_parser = subparsers.add_parser('stats', help='Show analytics and statistics')
    stats_parser.add_argument('--summary', action='store_true', help='Show overall summary')
    stats_parser.add_argument('--top-orchestras', type=int, default=10, help='Show top N orchestras')
    stats_parser.add_argument('--conductors', type=int, default=10, help='Show top N conductors')
    stats_parser.add_argument('--divisions', action='store_true', help='Show division statistics')
    stats_parser.add_argument('--years', action='store_true', help='Show yearly summary')
    stats_parser.add_argument('--start-year', type=int, help='Filter from this year')
    stats_parser.add_argument('--end-year', type=int, help='Filter until this year')

    # Streaming command
    streaming_parser = subparsers.add_parser('streaming', help='Discover streaming links for performances')
    streaming_parser.add_argument('--positions', type=Path, default=Path('apps/band-positions/public/data/band_positions.json'), help='Path to band positions dataset (JSON)')
    streaming_parser.add_argument('--output-dir', type=Path, default=Path('apps/band-positions/public/data/streaming'), help='Directory to store per-year streaming metadata')
    streaming_parser.add_argument('--aggregate', type=Path, default=Path('apps/band-positions/public/data/piece_streaming_links.json'), help='Combined JSON output consumed by the app')
    streaming_parser.add_argument('--min-year', type=int, default=2017, help='First year to include (default: 2017)')
    streaming_parser.add_argument('--years', nargs='+', type=int, help='Specific years to process')
    streaming_parser.add_argument('--start-year', type=int, help='Optional starting year filter')
    streaming_parser.add_argument('--end-year', type=int, help='Optional ending year filter')
    streaming_parser.add_argument('--credentials', type=Path, default=Path('config/streaming_credentials.json'), help='Path to local credentials JSON (ignored if missing)')
    streaming_parser.add_argument('--spotify-client-id', type=str, default=os.getenv('SPOTIFY_CLIENT_ID'))
    streaming_parser.add_argument('--spotify-client-secret', type=str, default=os.getenv('SPOTIFY_CLIENT_SECRET'))
    streaming_parser.add_argument('--overrides', type=Path, default=Path('config/streaming_overrides.json'), help='Path to overrides for known corrections')
    streaming_parser.add_argument('--cache', type=Path, default=Path('config/streaming_cache.json'), help='Path to cache previously fetched streaming metadata')
    streaming_parser.add_argument('--band-type', type=str, default='wind', choices=('wind', 'brass'), help='Dataset type to process (default: wind)')
    streaming_parser.add_argument('--apple-country', type=str, default='us', help='Apple Music storefront to target (default: us)')
    streaming_parser.add_argument('--skip-spotify', action='store_true', help='Skip Spotify search')
    streaming_parser.add_argument('--skip-apple', action='store_true', help='Skip Apple Music search')
    
    args = parser.parse_args()
    
    # Show banner
    show_banner()
    
    if not args.command:
        console.print("[yellow]No command specified. Use --help for usage information.[/yellow]")
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'pipeline':
        success = run_pipeline(args.years, args.force_refresh)
        sys.exit(0 if success else 1)
    
    elif args.command == 'urls':
        url_discovery = URLDiscovery()
        
        if args.show:
            urls = url_discovery.get_all_urls(args.force_refresh)
            console.print(f"[bold]Available URLs ({len(urls)}):[/bold]")
            for year, url in sorted(urls.items()):
                console.print(f"  {year}: {url}")
            console.print(f"\\nMissing years: {url_discovery.get_missing_years()}")
        else:
            urls = url_discovery.get_all_urls(args.force_refresh)
            console.print(f"✓ Discovered {len(urls)} URLs")
            console.print(f"Year range: {min(urls.keys())}-{max(urls.keys())}")
            console.print(f"Missing years: {url_discovery.get_missing_years()}")
    
    elif args.command == 'fetch':
        fetcher = HTMLFetcher()
        
        if args.stats:
            stats = fetcher.get_cache_stats()
            console.print("[bold]Cache Statistics:[/bold]")
            console.print(f"Cached files: {stats['total_cached_files']}")
            console.print(f"Total size: {stats['total_size_mb']} MB")
            console.print(f"Years: {stats['cached_years']}")
        elif args.all:
            fetcher.fetch_all_available_years(args.force_refresh)
        elif args.years:
            fetcher.fetch_multiple_years(args.years, args.force_refresh)
        else:
            console.print("[yellow]Please specify --all, --years, or --stats[/yellow]")
    
    elif args.command == 'parse':
        parser = JSONParser()
        parser.load_all_data(args.force_refresh)
        
        if args.all_years:
            years = parser.get_available_years()
            console.print(f"Available years: {years}")
            console.print(f"Total: {len(years)} years ({min(years)}-{max(years)})")
        elif args.year:
            result = parser.parse_year(args.year)
            console.print(f"Year {args.year}: {result.total_orchestras} orchestras in {len(result.divisions)} divisions")
            for div in result.divisions:
                console.print(f"  {div.name}: {len(div.placements)} orchestras")
        else:
            years = parser.get_available_years()
            console.print(f"Available years: {len(years)} ({min(years)}-{max(years)})")
    
    elif args.command == 'export':
        exporter = DataExporter()
        
        if args.stats:
            stats = exporter.get_export_stats()
            console.print("[bold]Export Statistics:[/bold]")
            console.print(f"CSV files: {stats['total_csv_files']}")
            console.print(f"JSON files: {stats['total_json_files']}")
            console.print(f"Total size: {stats['total_size_mb']} MB")
        elif args.all:
            result = exporter.export_all_years()
            console.print(f"✓ Exported {result['total_placements']} placements across {result['total_years']} years")
        elif args.years:
            result = exporter.export_all_years(args.years)
            console.print(f"✓ Exported {result['total_placements']} placements across {result['total_years']} years")
        elif args.year:
            exporter.parser.load_all_data()
            result = exporter.export_year(args.year)
            console.print(f"✓ Exported data for {args.year}")
        else:
            console.print("[yellow]Please specify --all, --years, --year, or --stats[/yellow]")
    
    elif args.command == 'stats':
        analytics = CompetitionAnalytics()
        
        if args.summary:
            stats = analytics.get_summary_stats()
            console.print("\\n[bold]Overall Statistics[/bold]")
            console.print(f"Total placements: {stats['total_placements']}")
            console.print(f"Years: {stats['total_years']} ({stats['year_range']})")
            console.print(f"Orchestras: {stats['total_orchestras']}")
            console.print(f"Conductors: {stats['total_conductors']}")
            console.print(f"Avg points: {stats['avg_points']:.2f}")
        
        if args.top_orchestras:
            table = analytics.get_top_orchestras(args.top_orchestras)
            console.print(table)
        
        if args.conductors:
            table = analytics.get_conductor_stats(args.conductors)
            console.print(table)
        
        if args.divisions:
            table = analytics.get_division_stats()
            console.print(table)
        
        if args.years:
            table = analytics.get_yearly_summary(args.start_year, args.end_year)
            console.print(table)
        
        if not any([args.summary, args.top_orchestras, args.conductors, args.divisions, args.years]):
            # Default: show summary and top orchestras
            console.print("[blue]Showing default analytics (use --help for more options)[/blue]")
            analytics.get_summary_stats()  # This will load data
            stats_table = analytics.get_top_orchestras(5)
            console.print(stats_table)

    elif args.command == 'streaming':
        generate_streaming_links(
            positions=args.positions,
            output_dir=args.output_dir,
            aggregate=args.aggregate,
            min_year=args.min_year,
            years=args.years,
            start_year=args.start_year,
            end_year=args.end_year,
            spotify_client_id=args.spotify_client_id,
            spotify_client_secret=args.spotify_client_secret,
            apple_country=args.apple_country,
            skip_spotify=args.skip_spotify,
            skip_apple=args.skip_apple,
            overrides_path=args.overrides,
            credentials_path=args.credentials,
            cache_path=args.cache,
            band_type=args.band_type,
            console=console,
        )


if __name__ == "__main__":
    main()
