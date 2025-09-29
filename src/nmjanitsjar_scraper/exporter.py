"""
Data exporter for Norwegian Wind Band Orchestra competition results.

This module exports structured competition data to CSV and JSON formats
for analysis and database integration.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

import pandas as pd
from rich.console import Console
from rich.progress import track

from .models import CompetitionYear, Division, Placement, Award
from .parser import JSONParser

console = Console()


class DataExporter:
    """Exports competition data to various formats."""
    
    def __init__(self, output_dir: Path = None, parser = None):
        """
        Initialize data exporter.
        
        Args:
            output_dir: Directory to write exported files
            parser: Parser instance (JSONParser or BrassXMLParser). If None, uses JSONParser.
        """
        self.output_dir = output_dir or Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parser = parser if parser is not None else JSONParser()
        
    def normalize_placement_data(self, placement: Placement, year: int, division: str) -> Dict[str, Any]:
        """
        Normalize placement data for export.
        
        Args:
            placement: Placement object to normalize
            year: Competition year
            division: Division name
            
        Returns:
            Normalized placement data as dictionary
        """
        # Generate unique ID
        division_slug = division.lower().replace(' ', '-').replace('.', '')
        rank_component = f"{int(placement.rank):02d}" if placement.rank is not None else "xx"
        orchestra_slug = placement.orchestra.lower().replace(' ', '-').replace('.', '') if placement.orchestra else "ukjent"
        placement_id = f"{year}-{division_slug}-{rank_component}-{orchestra_slug}"
        
        # Split composer from pieces if present
        pieces_with_composers = []
        composers = []
        
        for piece in placement.pieces:
            if " – " in piece or " - " in piece:
                # Split on em dash or regular dash
                parts = piece.split(" – ") if " – " in piece else piece.split(" - ")
                if len(parts) == 2:
                    piece_title = parts[0].strip()
                    composer = parts[1].strip()
                    pieces_with_composers.append(piece_title)
                    if composer not in composers:
                        composers.append(composer)
                else:
                    pieces_with_composers.append(piece.strip())
            else:
                pieces_with_composers.append(piece.strip())
        
        return {
            "id": placement_id,
            "year": year,
            "division": division,
            "rank": placement.rank,
            "orchestra": placement.orchestra.strip() if placement.orchestra else None,
            "conductor": placement.conductor.strip() if placement.conductor else None,
            "pieces": "; ".join(pieces_with_composers) if pieces_with_composers else None,
            "pieces_list": pieces_with_composers,
            "composers": "; ".join(composers) if composers else None,
            "composers_list": composers,
            "points": float(placement.points) if placement.points is not None else None,
            "max_points": 100.0,  # Assume max 100 points
            "image_url": placement.image_url,
            "orchestra_url": placement.orchestra_url,
            "conductor_url": placement.conductor_url,
            "piece_urls": "; ".join(placement.piece_urls) if placement.piece_urls else None,
            "scraped_at": datetime.now().isoformat()
        }
    
    def normalize_award_data(self, award: Award, year: int, division: str) -> Dict[str, Any]:
        """
        Normalize award data for export.
        
        Args:
            award: Award object to normalize
            year: Competition year
            division: Division name
            
        Returns:
            Normalized award data as dictionary
        """
        award_id = f"{year}-{division.lower().replace(' ', '-').replace('.', '')}-{award.award_type.lower()}"
        
        return {
            "id": award_id,
            "year": year,
            "division": division,
            "award_type": award.award_type,
            "recipient": award.recipient.strip() if award.recipient else None,
            "orchestra": award.orchestra.strip() if award.orchestra else None,
            "scraped_at": datetime.now().isoformat()
        }
    
    def export_year(self, year: int, competition_data: CompetitionYear = None) -> Dict[str, str]:
        """
        Export data for a specific year to CSV and JSON.
        
        Args:
            year: Competition year to export
            competition_data: Pre-parsed competition data (optional)
            
        Returns:
            Dictionary with paths to exported files
        """
        if competition_data is None:
            competition_data = self.parser.parse_year(year)
        
        console.print(f"[blue]Exporting data for year {year}[/blue]")
        
        # Normalize all placement data
        placements_data = []
        awards_data = []
        
        for division in competition_data.divisions:
            # Process placements
            for placement in division.placements:
                normalized_placement = self.normalize_placement_data(placement, year, division.name)
                placements_data.append(normalized_placement)
            
            # Process awards
            for award in division.awards:
                normalized_award = self.normalize_award_data(award, year, division.name)
                awards_data.append(normalized_award)
        
        # Export placements
        placements_file = self.output_dir / f"{year}_placements.csv"
        if placements_data:
            df_placements = pd.DataFrame(placements_data)
            df_placements.to_csv(placements_file, index=False, encoding='utf-8', lineterminator='\n')
            console.print(f"[green]✓ Exported {len(placements_data)} placements to {placements_file}[/green]")
        
        # Export awards (if any)
        awards_file = self.output_dir / f"{year}_awards.csv"
        if awards_data:
            df_awards = pd.DataFrame(awards_data)
            df_awards.to_csv(awards_file, index=False, encoding='utf-8', lineterminator='\n')
            console.print(f"[green]✓ Exported {len(awards_data)} awards to {awards_file}[/green]")
        else:
            # Create empty awards file for consistency
            with open(awards_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'year', 'division', 'award_type', 'recipient', 'orchestra', 'scraped_at'])
            console.print(f"[yellow]No awards data for {year}, created empty file[/yellow]")
        
        # Export JSON version for each year
        json_file = self.output_dir / f"{year}_complete.json"
        json_data = {
            "year": year,
            "total_orchestras": competition_data.total_orchestras,
            "total_divisions": len(competition_data.divisions),
            "divisions": [div.name for div in competition_data.divisions],
            "placements": placements_data,
            "awards": awards_data,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Exported complete data to {json_file}[/green]")
        
        return {
            "placements_csv": str(placements_file),
            "awards_csv": str(awards_file),
            "complete_json": str(json_file)
        }
    
    def export_all_years(self, years: List[int] = None) -> Dict[str, Any]:
        """
        Export data for all available years.
        
        Args:
            years: Specific years to export, or None for all available years
            
        Returns:
            Summary of exported data
        """
        # Load all data first
        self.parser.load_all_data()
        
        if years is None:
            years = self.parser.get_available_years()
        
        console.print(f"[bold]Exporting data for {len(years)} years[/bold]")
        
        all_placements = []
        all_awards = []
        year_summaries = {}
        
        for year in track(years, description="Exporting years..."):
            try:
                competition_data = self.parser.parse_year(year)
                exported_files = self.export_year(year, competition_data)
                
                # Collect data for master files
                for division in competition_data.divisions:
                    for placement in division.placements:
                        normalized_placement = self.normalize_placement_data(placement, year, division.name)
                        all_placements.append(normalized_placement)
                    
                    for award in division.awards:
                        normalized_award = self.normalize_award_data(award, year, division.name)
                        all_awards.append(normalized_award)
                
                year_summaries[year] = {
                    "total_orchestras": competition_data.total_orchestras,
                    "divisions": len(competition_data.divisions),
                    "exported_files": exported_files
                }
                
            except Exception as e:
                console.print(f"[red]Failed to export year {year}: {e}[/red]")
                year_summaries[year] = {"error": str(e)}
        
        # Create master files
        master_placements_file = self.output_dir / "all_placements.csv"
        if all_placements:
            df_all_placements = pd.DataFrame(all_placements)
            df_all_placements.to_csv(master_placements_file, index=False, encoding='utf-8', lineterminator='\n')
            console.print(f"[green]✓ Exported {len(all_placements)} total placements to {master_placements_file}[/green]")
        
        master_awards_file = self.output_dir / "all_awards.csv"
        if all_awards:
            df_all_awards = pd.DataFrame(all_awards)
            df_all_awards.to_csv(master_awards_file, index=False, encoding='utf-8', lineterminator='\n')
            console.print(f"[green]✓ Exported {len(all_awards)} total awards to {master_awards_file}[/green]")
        else:
            # Create empty master awards file
            with open(master_awards_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'year', 'division', 'award_type', 'recipient', 'orchestra', 'scraped_at'])
            console.print("[yellow]No awards data found, created empty master awards file[/yellow]")
        
        # Create master JSON file
        master_json_file = self.output_dir / "all_data.json"
        master_data = {
            "total_years": len(years),
            "year_range": f"{min(years)}-{max(years)}",
            "total_placements": len(all_placements),
            "total_awards": len(all_awards),
            "years_summary": year_summaries,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(master_json_file, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Exported master data summary to {master_json_file}[/green]")
        
        # Also create a records-oriented JSON for easy database import
        records_json_file = self.output_dir / "all_placements_records.json"
        if all_placements:
            with open(records_json_file, 'w', encoding='utf-8') as f:
                json.dump(all_placements, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓ Exported placement records to {records_json_file}[/green]")
        
        return {
            "total_years": len(years),
            "total_placements": len(all_placements),
            "total_awards": len(all_awards),
            "master_files": {
                "placements_csv": str(master_placements_file),
                "awards_csv": str(master_awards_file),
                "summary_json": str(master_json_file),
                "records_json": str(records_json_file)
            },
            "year_summaries": year_summaries
        }
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exported files."""
        csv_files = list(self.output_dir.glob("*.csv"))
        json_files = list(self.output_dir.glob("*.json"))
        
        stats = {
            "total_csv_files": len(csv_files),
            "total_json_files": len(json_files),
            "total_size_mb": 0,
            "files": []
        }
        
        for file_path in csv_files + json_files:
            file_size = file_path.stat().st_size
            stats["total_size_mb"] += file_size
            stats["files"].append({
                "name": file_path.name,
                "size_kb": round(file_size / 1024, 2),
                "type": file_path.suffix[1:]  # Remove the dot
            })
        
        stats["total_size_mb"] = round(stats["total_size_mb"] / (1024 * 1024), 2)
        stats["files"].sort(key=lambda x: x["size_kb"], reverse=True)
        
        return stats


def main():
    """CLI entry point for data export."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export Norwegian Wind Band Orchestra competition data")
    parser.add_argument("--year", type=int, help="Specific year to export")
    parser.add_argument("--years", nargs="+", type=int, help="Specific years to export")
    parser.add_argument("--all", action="store_true", help="Export all available years")
    parser.add_argument("--stats", action="store_true", help="Show export statistics")
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    if args.stats:
        stats = exporter.get_export_stats()
        console.print("[bold]Export Statistics:[/bold]")
        console.print(f"CSV files: {stats['total_csv_files']}")
        console.print(f"JSON files: {stats['total_json_files']}")
        console.print(f"Total size: {stats['total_size_mb']} MB")
        console.print("\n[bold]Largest files:[/bold]")
        for file_info in stats["files"][:10]:
            console.print(f"  {file_info['name']}: {file_info['size_kb']} KB ({file_info['type']})")
        return
    
    if args.all:
        result = exporter.export_all_years()
        console.print(f"\n[bold green]Export completed![/bold green]")
        console.print(f"Years: {result['total_years']}")
        console.print(f"Placements: {result['total_placements']}")
        console.print(f"Awards: {result['total_awards']}")
    elif args.years:
        result = exporter.export_all_years(args.years)
        console.print(f"\n[bold green]Export completed![/bold green]")
        console.print(f"Years: {result['total_years']}")
        console.print(f"Placements: {result['total_placements']}")
    elif args.year:
        # Load parser data first
        exporter.parser.load_all_data()
        result = exporter.export_year(args.year)
        console.print(f"\n[bold green]Export completed for {args.year}![/bold green]")
        console.print(f"Files: {list(result.values())}")
    else:
        console.print("[red]Please specify --year, --years, or --all[/red]")
        parser.print_help()


if __name__ == "__main__":
    main()
