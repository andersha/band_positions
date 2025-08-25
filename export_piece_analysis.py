#!/usr/bin/env python3
"""
Export piece analysis results to CSV and JSON formats.

This script generates comprehensive reports on musical piece popularity,
success rates, and enriched metadata from WindRep.org integration.
"""

import json
import csv
from pathlib import Path
from datetime import datetime

from src.nmjanitsjar_scraper.piece_analysis import PieceAnalyzer
from rich.console import Console

console = Console()


def export_piece_analysis():
    """Export piece analysis results to data files."""
    
    console.print("[bold blue]🎵 Exporting Musical Piece Analysis Results[/bold blue]")
    
    # Initialize analyzer
    analyzer = PieceAnalyzer()
    
    # Create output directory
    output_dir = Path("data/piece_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Get comprehensive piece analysis
    console.print("\n[blue]Analyzing all pieces across 40+ years of competitions...[/blue]")
    all_pieces = analyzer.analyze_piece_popularity()
    
    console.print(f"✓ Analyzed {len(all_pieces)} unique pieces")
    
    # 2. Get popular pieces (minimum 3 performances)
    popular_pieces = analyzer.get_most_popular_pieces(min_performances=3)
    console.print(f"✓ Found {len(popular_pieces)} popular pieces (3+ performances)")
    
    # 3. Get successful pieces (minimum 2 performances)
    successful_pieces = analyzer.get_highest_success_pieces(min_performances=2)
    console.print(f"✓ Found {len(successful_pieces)} pieces with success data")
    
    # 4. Enrich top pieces with WindRep data
    console.print("\n[blue]Enriching top 25 pieces with WindRep.org metadata...[/blue]")
    enriched_pieces = analyzer.enrich_with_windrep_data(popular_pieces[:25], max_pieces=25)
    
    # 5. Export to CSV files
    console.print("\n[blue]Exporting to CSV files...[/blue]")
    
    # Export all pieces CSV
    all_pieces_csv = output_dir / f"all_pieces_{timestamp}.csv"
    with open(all_pieces_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'title', 'composer', 'performances', 'wins', 'win_rate_percent', 
            'avg_points', 'duration_minutes', 'difficulty', 'grade_level', 'category', 'windrep_url'
        ])
        
        for piece in all_pieces.values():
            writer.writerow([
                piece.title,
                piece.composer,
                piece.performance_count,
                int(piece.performance_count * piece.win_rate / 100),
                round(piece.win_rate, 2),
                round(piece.avg_points, 2) if piece.avg_points else None,
                piece.duration_minutes,
                piece.difficulty,
                piece.grade_level,
                piece.category,
                piece.windrep_url
            ])
    
    console.print(f"✓ Exported all pieces to {all_pieces_csv}")
    
    # Export popular pieces CSV (enriched)
    popular_csv = output_dir / f"popular_pieces_{timestamp}.csv"
    with open(popular_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'rank', 'title', 'composer', 'performances', 'wins', 'win_rate_percent', 
            'avg_points', 'duration_minutes', 'difficulty', 'grade_level', 'category', 'windrep_url'
        ])
        
        for i, piece in enumerate(enriched_pieces, 1):
            writer.writerow([
                i,
                piece.title,
                piece.composer,
                piece.performance_count,
                int(piece.performance_count * piece.win_rate / 100),
                round(piece.win_rate, 2),
                round(piece.avg_points, 2) if piece.avg_points else None,
                piece.duration_minutes,
                piece.difficulty,
                piece.grade_level,
                piece.category,
                piece.windrep_url
            ])
    
    console.print(f"✓ Exported top popular pieces to {popular_csv}")
    
    # Export successful pieces CSV
    successful_csv = output_dir / f"successful_pieces_{timestamp}.csv"
    with open(successful_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'rank', 'title', 'composer', 'performances', 'wins', 'win_rate_percent', 
            'avg_points', 'duration_minutes', 'difficulty', 'grade_level', 'category', 'windrep_url'
        ])
        
        for i, piece in enumerate(successful_pieces[:50], 1):
            writer.writerow([
                i,
                piece.title,
                piece.composer,
                piece.performance_count,
                int(piece.performance_count * piece.win_rate / 100),
                round(piece.win_rate, 2),
                round(piece.avg_points, 2) if piece.avg_points else None,
                piece.duration_minutes,
                piece.difficulty,
                piece.grade_level,
                piece.category,
                piece.windrep_url
            ])
    
    console.print(f"✓ Exported top successful pieces to {successful_csv}")
    
    # 6. Export to JSON
    console.print("\n[blue]Exporting to JSON files...[/blue]")
    
    # Comprehensive analysis JSON
    analysis_json = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_unique_pieces": len(all_pieces),
            "popular_pieces_threshold": 3,
            "successful_pieces_threshold": 2,
            "windrep_enriched_count": sum(1 for p in enriched_pieces if p.windrep_url)
        },
        "statistics": {
            "total_performances": sum(p.performance_count for p in all_pieces.values()),
            "avg_performances_per_piece": sum(p.performance_count for p in all_pieces.values()) / len(all_pieces),
            "pieces_with_wins": sum(1 for p in all_pieces.values() if p.win_rate > 0),
            "pieces_with_duration_data": sum(1 for p in enriched_pieces if p.duration_minutes),
        },
        "popular_pieces": [
            {
                "rank": i,
                "title": piece.title,
                "composer": piece.composer,
                "performances": piece.performance_count,
                "wins": int(piece.performance_count * piece.win_rate / 100),
                "win_rate_percent": round(piece.win_rate, 2),
                "avg_points": round(piece.avg_points, 2) if piece.avg_points else None,
                "duration_minutes": piece.duration_minutes,
                "difficulty": piece.difficulty,
                "grade_level": piece.grade_level,
                "category": piece.category,
                "windrep_url": piece.windrep_url
            }
            for i, piece in enumerate(enriched_pieces, 1)
        ],
        "successful_pieces": [
            {
                "rank": i,
                "title": piece.title,
                "composer": piece.composer,
                "performances": piece.performance_count,
                "wins": int(piece.performance_count * piece.win_rate / 100),
                "win_rate_percent": round(piece.win_rate, 2),
                "avg_points": round(piece.avg_points, 2) if piece.avg_points else None,
                "duration_minutes": piece.duration_minutes,
                "difficulty": piece.difficulty,
                "grade_level": piece.grade_level,
                "category": piece.category,
                "windrep_url": piece.windrep_url
            }
            for i, piece in enumerate(successful_pieces[:50], 1)
        ]
    }
    
    analysis_json_file = output_dir / f"piece_analysis_{timestamp}.json"
    with open(analysis_json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_json, f, indent=2, ensure_ascii=False)
    
    console.print(f"✓ Exported comprehensive analysis to {analysis_json_file}")
    
    # Create latest files (symlinks to most recent)
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(exist_ok=True)
    
    # Summary report
    console.print("\n[bold green]📊 Analysis Summary[/bold green]")
    console.print(f"• Total unique pieces analyzed: {len(all_pieces):,}")
    console.print(f"• Popular pieces (3+ performances): {len(popular_pieces):,}")  
    console.print(f"• Pieces with success data: {len(successful_pieces):,}")
    console.print(f"• WindRep.org enriched pieces: {sum(1 for p in enriched_pieces if p.windrep_url):,}")
    console.print(f"• Pieces with duration data: {sum(1 for p in enriched_pieces if p.duration_minutes):,}")
    
    total_performances = sum(p.performance_count for p in all_pieces.values())
    avg_performances = total_performances / len(all_pieces)
    console.print(f"• Total performances tracked: {total_performances:,}")
    console.print(f"• Average performances per piece: {avg_performances:.1f}")
    
    console.print(f"\n[bold blue]📁 Files exported to: {output_dir}[/bold blue]")
    
    return {
        "output_dir": output_dir,
        "files_created": [
            all_pieces_csv.name,
            popular_csv.name, 
            successful_csv.name,
            analysis_json_file.name
        ],
        "statistics": analysis_json["statistics"]
    }


if __name__ == "__main__":
    export_piece_analysis()
