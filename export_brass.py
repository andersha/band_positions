#!/usr/bin/env python3
"""
Export brass band competition data from nmbrass.no.

This script fetches and exports all available brass band competition data
to CSV and JSON formats, similar to the existing wind band data export.
"""

from pathlib import Path
from src.nmjanitsjar_scraper.brass_parser import BrassXMLParser
from src.nmjanitsjar_scraper.exporter import DataExporter
from rich.console import Console

console = Console()


def main():
    """Main export function for brass band data."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export Norwegian Brass Band competition data from nmbrass.no"
    )
    parser.add_argument(
        "--year", 
        type=int, 
        help="Export specific year only"
    )
    parser.add_argument(
        "--years", 
        nargs="+", 
        type=int, 
        help="Export specific years"
    )
    parser.add_argument(
        "--force-refresh", 
        action="store_true", 
        help="Force refresh cached XML data"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("data/brass/processed"),
        help="Output directory for exported files (default: data/brass/processed)"
    )
    
    args = parser.parse_args()
    
    console.print("[bold magenta]🎺 Brass Band Data Exporter 🎺[/bold magenta]\n")
    
    # Initialize brass parser
    console.print("[blue]Step 1: Loading brass band data from nmbrass.no[/blue]")
    brass_parser = BrassXMLParser()
    brass_parser.load_all_data(force_refresh=args.force_refresh)
    
    available_years = brass_parser.get_available_years()
    console.print(f"[green]✓ Found data for {len(available_years)} years: {min(available_years)}-{max(available_years)}[/green]\n")
    
    # Initialize exporter with brass parser
    console.print(f"[blue]Step 2: Exporting data to {args.output_dir}[/blue]")
    exporter = DataExporter(output_dir=args.output_dir, parser=brass_parser)
    
    # Determine which years to export
    if args.year:
        years_to_export = [args.year]
    elif args.years:
        years_to_export = args.years
    else:
        years_to_export = None  # Export all
    
    # Export data
    result = exporter.export_all_years(years=years_to_export)
    
    console.print("\n[bold green]🎉 Export completed successfully![/bold green]")
    console.print(f"  • Years exported: {result['total_years']}")
    console.print(f"  • Total placements: {result['total_placements']}")
    console.print(f"  • Total awards: {result['total_awards']}")
    console.print(f"\n[bold]Output files:[/bold]")
    console.print(f"  • Master CSV: {result['master_files']['placements_csv']}")
    console.print(f"  • Master JSON: {result['master_files']['summary_json']}")
    console.print(f"  • Records JSON: {result['master_files']['records_json']}")
    
    # Show some sample data
    console.print(f"\n[bold]Sample year summaries:[/bold]")
    for year in sorted(result['year_summaries'].keys())[:3]:
        summary = result['year_summaries'][year]
        if 'error' not in summary:
            console.print(f"  • {year}: {summary['total_orchestras']} orchestras, {summary['divisions']} divisions")


if __name__ == "__main__":
    main()