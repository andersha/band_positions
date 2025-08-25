"""
Analytics module for Norwegian Wind Band Orchestra competition data.

This module provides basic statistical analysis and visualization of
the competition data.
"""

from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


class CompetitionAnalytics:
    """Provides analytics for competition data."""
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize analytics with data directory.
        
        Args:
            data_dir: Directory containing processed CSV files
        """
        self.data_dir = data_dir or Path("data/processed")
        self.placements_df = None
        
    def load_data(self) -> None:
        """Load all placement data into memory."""
        master_file = self.data_dir / "all_placements.csv"
        
        if not master_file.exists():
            console.print(f"[red]No master data file found at {master_file}[/red]")
            console.print("[yellow]Please run the exporter first to generate CSV files[/yellow]")
            return
        
        console.print("[blue]Loading placement data...[/blue]")
        self.placements_df = pd.read_csv(master_file)
        
        # Convert year to int and points to float
        self.placements_df['year'] = self.placements_df['year'].astype(int)
        self.placements_df['points'] = pd.to_numeric(self.placements_df['points'], errors='coerce')
        
        console.print(f"[green]✓ Loaded {len(self.placements_df)} placements[/green]")
    
    def get_top_orchestras(self, limit: int = 10) -> Table:
        """Get top performing orchestras by number of wins."""
        if self.placements_df is None:
            self.load_data()
        
        # Count wins (rank = 1) by orchestra
        wins = self.placements_df[self.placements_df['rank'] == 1]['orchestra'].value_counts()
        
        table = Table(title=f"Top {limit} Orchestras by Wins")
        table.add_column("Orchestra", style="cyan", no_wrap=True)
        table.add_column("Wins", style="magenta")
        table.add_column("Last Win", style="green")
        
        for orchestra, win_count in wins.head(limit).items():
            # Find last win year
            last_win_data = self.placements_df[
                (self.placements_df['orchestra'] == orchestra) & 
                (self.placements_df['rank'] == 1)
            ]
            last_win = last_win_data['year'].max()
            
            table.add_row(str(orchestra), str(win_count), str(last_win))
        
        return table
    
    def get_division_stats(self) -> Table:
        """Get statistics by division."""
        if self.placements_df is None:
            self.load_data()
        
        table = Table(title="Division Statistics")
        table.add_column("Division", style="cyan")
        table.add_column("Total Orchestras", style="magenta")
        table.add_column("Years Active", style="green")
        table.add_column("Avg Points", style="yellow")
        
        for division in sorted(self.placements_df['division'].unique()):
            div_data = self.placements_df[self.placements_df['division'] == division]
            
            total_orchestras = len(div_data)
            years_active = div_data['year'].nunique()
            avg_points = div_data['points'].mean()
            
            table.add_row(
                division,
                str(total_orchestras),
                str(years_active),
                f"{avg_points:.1f}" if pd.notna(avg_points) else "N/A"
            )
        
        return table
    
    def get_yearly_summary(self, start_year: int = None, end_year: int = None) -> Table:
        """Get yearly summary statistics."""
        if self.placements_df is None:
            self.load_data()
        
        df = self.placements_df.copy()
        
        if start_year:
            df = df[df['year'] >= start_year]
        if end_year:
            df = df[df['year'] <= end_year]
        
        table = Table(title="Yearly Summary")
        table.add_column("Year", style="cyan")
        table.add_column("Orchestras", style="magenta")
        table.add_column("Divisions", style="green")
        table.add_column("Avg Points", style="yellow")
        table.add_column("Elite Winner", style="bold blue")
        
        for year in sorted(df['year'].unique()):
            year_data = df[df['year'] == year]
            
            total_orchestras = len(year_data)
            total_divisions = year_data['division'].nunique()
            avg_points = year_data['points'].mean()
            
            # Find Elite winner
            elite_winner = "N/A"
            elite_data = year_data[
                (year_data['division'] == 'Elite') & 
                (year_data['rank'] == 1)
            ]
            if not elite_data.empty:
                elite_winner = elite_data.iloc[0]['orchestra']
                # Truncate long names
                if len(elite_winner) > 25:
                    elite_winner = elite_winner[:22] + "..."
            
            table.add_row(
                str(year),
                str(total_orchestras),
                str(total_divisions),
                f"{avg_points:.1f}" if pd.notna(avg_points) else "N/A",
                elite_winner
            )
        
        return table
    
    def get_conductor_stats(self, limit: int = 10) -> Table:
        """Get top conductors by wins."""
        if self.placements_df is None:
            self.load_data()
        
        # Count wins by conductor (exclude null conductors)
        conductor_data = self.placements_df[
            (self.placements_df['rank'] == 1) & 
            (self.placements_df['conductor'].notna())
        ]
        
        wins = conductor_data['conductor'].value_counts()
        
        table = Table(title=f"Top {limit} Conductors by Wins")
        table.add_column("Conductor", style="cyan", no_wrap=True)
        table.add_column("Wins", style="magenta")
        table.add_column("Orchestras", style="green")
        
        for conductor, win_count in wins.head(limit).items():
            # Find orchestras conducted
            orchestras = conductor_data[
                conductor_data['conductor'] == conductor
            ]['orchestra'].unique()
            
            orchestras_str = ", ".join(orchestras[:3])  # Show first 3
            if len(orchestras) > 3:
                orchestras_str += f" (+{len(orchestras)-3} more)"
            
            table.add_row(str(conductor), str(win_count), orchestras_str)
        
        return table
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get overall summary statistics."""
        if self.placements_df is None:
            self.load_data()
        
        df = self.placements_df
        
        return {
            "total_placements": len(df),
            "total_years": df['year'].nunique(),
            "year_range": f"{df['year'].min()}-{df['year'].max()}",
            "total_orchestras": df['orchestra'].nunique(),
            "total_conductors": df['conductor'].nunique(),
            "total_divisions": df['division'].nunique(),
            "avg_points": df['points'].mean(),
            "min_points": df['points'].min(),
            "max_points": df['points'].max(),
        }


def main():
    """CLI entry point for analytics."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Norwegian Wind Band Orchestra competition data")
    parser.add_argument("--top-orchestras", type=int, default=10, help="Show top N orchestras")
    parser.add_argument("--divisions", action="store_true", help="Show division statistics")
    parser.add_argument("--years", action="store_true", help="Show yearly summary")
    parser.add_argument("--conductors", type=int, default=10, help="Show top N conductors")
    parser.add_argument("--summary", action="store_true", help="Show overall summary")
    parser.add_argument("--start-year", type=int, help="Filter from this year")
    parser.add_argument("--end-year", type=int, help="Filter until this year")
    
    args = parser.parse_args()
    
    analytics = CompetitionAnalytics()
    
    if args.summary:
        stats = analytics.get_summary_stats()
        console.print("\n[bold]Overall Statistics[/bold]")
        console.print(f"Total placements: {stats['total_placements']}")
        console.print(f"Years covered: {stats['total_years']} ({stats['year_range']})")
        console.print(f"Unique orchestras: {stats['total_orchestras']}")
        console.print(f"Unique conductors: {stats['total_conductors']}")
        console.print(f"Divisions: {stats['total_divisions']}")
        console.print(f"Average points: {stats['avg_points']:.2f}")
        console.print(f"Point range: {stats['min_points']:.1f} - {stats['max_points']:.1f}")
        console.print()
    
    if args.top_orchestras:
        table = analytics.get_top_orchestras(args.top_orchestras)
        console.print(table)
        console.print()
    
    if args.conductors:
        table = analytics.get_conductor_stats(args.conductors)
        console.print(table)
        console.print()
    
    if args.divisions:
        table = analytics.get_division_stats()
        console.print(table)
        console.print()
    
    if args.years:
        table = analytics.get_yearly_summary(args.start_year, args.end_year)
        console.print(table)


if __name__ == "__main__":
    main()
