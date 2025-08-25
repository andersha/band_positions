"""
Musical piece popularity analysis for Norwegian Wind Band Orchestra competitions.

This module analyzes piece performance data, integrates with WindRep.org for 
detailed piece information, and provides insights on optimal program selection
based on division time constraints.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import Counter, defaultdict
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import track

from .parser import JSONParser

console = Console()


@dataclass
class PieceInfo:
    """Information about a musical piece."""
    title: str
    composer: str
    duration_minutes: Optional[float] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    windrep_url: Optional[str] = None
    performance_count: int = 0
    win_rate: float = 0.0
    avg_points: Optional[float] = None


@dataclass
class DivisionConstraints:
    """Time constraints for each division."""
    name: str
    max_minutes: int
    max_pieces: Optional[int] = None
    
    @classmethod
    def get_constraints(cls) -> Dict[str, 'DivisionConstraints']:
        """Get division time constraints from the rules."""
        return {
            "Elite": cls("Elite", 35),
            "1. divisjon": cls("1. divisjon", 25),
            "2. divisjon": cls("2. divisjon", 20),
            "3. divisjon": cls("3. divisjon", 15, 3),
            "4. divisjon": cls("4. divisjon", 15, 3),
            "5. divisjon": cls("5. divisjon", 15, 3),
            "6. divisjon": cls("6. divisjon", 15, 3),
            "7. divisjon": cls("7. divisjon", 15, 3),
        }


class WindRepScraper:
    """Scraper for WindRep.org to get piece information."""
    
    BASE_URL = "https://www.windrep.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Norwegian Band Competition Analyzer/1.0 (Research Project)'
        })
        self.cache = {}
        
    def search_piece(self, title: str, composer: str = None) -> Optional[Dict]:
        """
        Search for a piece on WindRep.org.
        
        Args:
            title: Piece title
            composer: Composer name (optional)
            
        Returns:
            Dictionary with piece information or None if not found
        """
        # Create cache key
        cache_key = f"{title}|{composer or ''}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Use MediaWiki search API
            search_params = {
                'action': 'opensearch',
                'search': title,
                'limit': 10,
                'namespace': 0,
                'format': 'json'
            }
            
            search_url = f"{self.BASE_URL}/api.php"
            response = self.session.get(search_url, params=search_params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                if len(results) >= 2 and results[1]:  # results[1] contains titles
                    # Look for best match
                    for i, result_title in enumerate(results[1]):
                        if self._is_good_match(title, result_title, composer):
                            page_url = results[3][i] if len(results) > 3 else f"{self.BASE_URL}/wiki/{result_title.replace(' ', '_')}"
                            piece_info = self._extract_piece_info(page_url, result_title)
                            self.cache[cache_key] = piece_info
                            return piece_info
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            console.print(f"[yellow]WindRep search failed for '{title}': {e}[/yellow]")
        
        self.cache[cache_key] = None
        return None
    
    def _is_good_match(self, search_title: str, result_title: str, composer: str = None) -> bool:
        """Check if a search result is a good match for the piece."""
        # Normalize strings for comparison
        search_clean = re.sub(r'[^\w\s]', '', search_title.lower())
        result_clean = re.sub(r'[^\w\s]', '', result_title.lower())
        
        # Check title similarity - this is the primary match criteria
        if search_clean in result_clean or result_clean in search_clean:
            return True
        
        # Also check for exact matches and common variations
        if search_clean == result_clean:
            return True
        
        # Check for partial matches in case of longer titles
        search_words = set(search_clean.split())
        result_words = set(result_clean.split())
        
        # If most words match, consider it a good match
        if len(search_words) > 1 and len(search_words.intersection(result_words)) >= len(search_words) * 0.7:
            return True
        
        return False
    
    def _extract_piece_info(self, page_url: str, title: str) -> Dict:
        """Extract piece information from WindRep page."""
        try:
            response = self.session.get(page_url, timeout=10)
            if response.status_code != 200:
                return {"title": title, "url": page_url}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            info = {
                "title": title,
                "url": page_url,
                "composer": None,
                "duration_minutes": None,
                "difficulty": None,
                "category": None
            }
            
            # Look for infobox or structured data
            infobox = soup.find('table', class_='infobox') or soup.find('div', class_='infobox')
            if infobox:
                info.update(self._parse_infobox(infobox))
            
            # Look for duration in various formats
            content = soup.get_text()
            duration = self._extract_duration(content)
            if duration:
                info["duration_minutes"] = duration
            
            return info
            
        except Exception as e:
            console.print(f"[yellow]Failed to extract info from {page_url}: {e}[/yellow]")
            return {"title": title, "url": page_url}
    
    def _parse_infobox(self, infobox) -> Dict:
        """Parse infobox data from WikiMedia page."""
        info = {}
        rows = infobox.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text().strip().lower()
                value = cells[1].get_text().strip()
                
                if 'composer' in key:
                    info['composer'] = value
                elif 'duration' in key or 'length' in key:
                    duration = self._extract_duration(value)
                    if duration:
                        info['duration_minutes'] = duration
                elif 'difficulty' in key or 'grade' in key:
                    info['difficulty'] = value
                elif 'genre' in key or 'category' in key:
                    info['category'] = value
        
        return info
    
    def _extract_duration(self, text: str) -> Optional[float]:
        """Extract duration in minutes from text."""
        # Look for patterns like "12:30", "12 minutes", "12'30\"", etc.
        patterns = [
            r'(\d+):(\d+)',  # 12:30 format
            r'(\d+)\s*(?:min|minutes?|m)\s*(\d+)?\s*(?:sec|seconds?|s)?',  # 12 minutes 30 seconds
            r"(\d+)'(\d+)\"",  # 12'30" format
            r'(\d+)\s*(?:min|minutes?)',  # Just minutes
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                match = matches[0]
                if isinstance(match, tuple) and len(match) == 2:
                    minutes = int(match[0]) if match[0] else 0
                    seconds = int(match[1]) if match[1] else 0
                    return minutes + seconds / 60
                elif isinstance(match, str):
                    return float(match)
        
        return None


class PieceAnalyzer:
    """Analyzes musical piece performance data."""
    
    def __init__(self, data_dir: Path = None):
        """Initialize piece analyzer."""
        self.data_dir = data_dir or Path("data/processed")
        self.parser = JSONParser()
        self.windrep = WindRepScraper()
        self.constraints = DivisionConstraints.get_constraints()
        
    def analyze_piece_popularity(self) -> Dict[str, PieceInfo]:
        """
        Analyze piece popularity across all competitions.
        
        Returns:
            Dictionary mapping piece titles to PieceInfo objects
        """
        console.print("[blue]Analyzing piece popularity across 40+ years of competitions...[/blue]")
        
        # Load all data
        self.parser.load_all_data()
        
        # Build repertoire to piece mapping from repmus data
        repertoire_to_piece = {}
        for item in self.parser._repmus.get("repmus", []):
            rep_nr = item.get("repertoarnr")
            piece_nr = item.get("musikkstykkenr")
            if rep_nr and piece_nr:
                repertoire_to_piece[rep_nr] = piece_nr
        
        console.print(f"✓ Loaded {len(repertoire_to_piece)} repertoire-to-piece mappings")
        
        # Get piece information from JSON
        pieces_lookup = {}
        for piece in self.parser._musikkstykker.get("musikkstykker", []):
            piece_id = piece.get("musikkstykkenr")
            if piece_id:
                pieces_lookup[piece_id] = {
                    "title": piece.get("tittel", "Unknown"),
                    "composer": piece.get("komponist", "Unknown")
                }
        
        console.print(f"✓ Loaded {len(pieces_lookup)} pieces from database")
        
        # Analyze performance data
        piece_stats = defaultdict(lambda: {
            "performances": 0,
            "wins": 0,
            "total_points": 0,
            "point_count": 0,
            "divisions": set(),
            "years": set()
        })
        
        # Get all competition data
        for comp in self.parser._konkurranser.get("konkurranser", []):
            repertoire_id = comp.get("repertoarnr")
            rank = comp.get("plassering", 999)
            points_raw = comp.get("poengtotalt")
            division = comp.get("divisjon", "Unknown")
            year = comp.get("aarstall")
            
            # Convert points to float if present
            points = None
            if points_raw is not None:
                try:
                    points = float(points_raw) if points_raw != "" else None
                except (ValueError, TypeError):
                    points = None
            
            # Map repertoire ID to piece ID using repmus
            if repertoire_id and repertoire_id in repertoire_to_piece:
                piece_id = repertoire_to_piece[repertoire_id]
                
                if piece_id in pieces_lookup:
                    piece_key = f"{pieces_lookup[piece_id]['title']}|{pieces_lookup[piece_id]['composer']}"
                    
                    stats = piece_stats[piece_key]
                    stats["performances"] += 1
                    if rank == 1:
                        stats["wins"] += 1
                    if points is not None:
                        stats["total_points"] += points
                        stats["point_count"] += 1
                    stats["divisions"].add(division)
                    stats["years"].add(year)
        
        # Create PieceInfo objects
        piece_infos = {}
        
        for piece_key, stats in piece_stats.items():
            title, composer = piece_key.split("|", 1)
            
            win_rate = (stats["wins"] / stats["performances"]) * 100 if stats["performances"] > 0 else 0
            avg_points = stats["total_points"] / stats["point_count"] if stats["point_count"] > 0 else None
            
            piece_info = PieceInfo(
                title=title,
                composer=composer,
                performance_count=stats["performances"],
                win_rate=win_rate,
                avg_points=avg_points
            )
            
            piece_infos[piece_key] = piece_info
        
        console.print(f"✓ Analyzed {len(piece_infos)} unique pieces")
        return piece_infos
    
    def get_most_popular_pieces(self, min_performances: int = 3) -> List[PieceInfo]:
        """Get most popular pieces by performance count."""
        pieces = self.analyze_piece_popularity()
        
        # Filter and sort
        popular_pieces = [
            piece for piece in pieces.values() 
            if piece.performance_count >= min_performances
        ]
        
        return sorted(popular_pieces, key=lambda p: p.performance_count, reverse=True)
    
    def get_highest_success_pieces(self, min_performances: int = 2) -> List[PieceInfo]:
        """Get pieces with highest win rates."""
        pieces = self.analyze_piece_popularity()
        
        # Filter and sort
        successful_pieces = [
            piece for piece in pieces.values() 
            if piece.performance_count >= min_performances
        ]
        
        return sorted(successful_pieces, key=lambda p: p.win_rate, reverse=True)
    
    def enrich_with_windrep_data(self, pieces: List[PieceInfo], max_pieces: int = 50) -> List[PieceInfo]:
        """
        Enrich piece data with information from WindRep.org.
        
        Args:
            pieces: List of PieceInfo objects to enrich
            max_pieces: Maximum number of pieces to enrich (for rate limiting)
            
        Returns:
            List of enriched PieceInfo objects
        """
        console.print(f"[blue]Enriching top {min(len(pieces), max_pieces)} pieces with WindRep.org data...[/blue]")
        
        enriched_pieces = []
        
        for piece in track(pieces[:max_pieces], description="Fetching piece details..."):
            windrep_info = self.windrep.search_piece(piece.title, piece.composer)
            
            if windrep_info:
                # Update piece with WindRep data
                piece.duration_minutes = windrep_info.get("duration_minutes") or piece.duration_minutes
                piece.difficulty = windrep_info.get("difficulty") or piece.difficulty
                piece.category = windrep_info.get("category") or piece.category
                piece.windrep_url = windrep_info.get("url")
            
            enriched_pieces.append(piece)
        
        console.print(f"✓ Enriched {len(enriched_pieces)} pieces with external data")
        return enriched_pieces
    
    def analyze_program_optimization(self, division: str = "Elite") -> Dict:
        """
        Analyze how orchestras optimize their programs within time constraints.
        
        Args:
            division: Division to analyze
            
        Returns:
            Analysis results for program optimization
        """
        constraints = self.constraints.get(division)
        if not constraints:
            console.print(f"[red]Unknown division: {division}[/red]")
            return {}
        
        console.print(f"[blue]Analyzing program optimization for {division} (max {constraints.max_minutes} minutes)[/blue]")
        
        # This would require piece duration data from WindRep
        # For now, return structure for future implementation
        return {
            "division": division,
            "constraints": constraints,
            "analysis": "Requires duration data from WindRep integration"
        }


def main():
    """CLI entry point for piece analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze musical piece popularity and success rates")
    parser.add_argument("--popular", type=int, default=20, help="Show top N popular pieces")
    parser.add_argument("--successful", type=int, default=20, help="Show top N successful pieces")
    parser.add_argument("--min-performances", type=int, default=2, help="Minimum performances to include")
    parser.add_argument("--enrich-windrep", action="store_true", help="Enrich data with WindRep.org")
    parser.add_argument("--max-enrich", type=int, default=20, help="Max pieces to enrich with WindRep")
    
    args = parser.parse_args()
    
    analyzer = PieceAnalyzer()
    
    if args.popular:
        console.print(f"\n[bold]🎵 Top {args.popular} Most Popular Pieces[/bold]")
        popular = analyzer.get_most_popular_pieces(args.min_performances)
        
        if args.enrich_windrep:
            popular = analyzer.enrich_with_windrep_data(popular, args.max_enrich)
        
        table = Table()
        table.add_column("Rank", style="cyan")
        table.add_column("Piece", style="green")
        table.add_column("Composer", style="blue")
        table.add_column("Performances", style="magenta")
        table.add_column("Win Rate %", style="red")
        table.add_column("Avg Points", style="yellow")
        if args.enrich_windrep:
            table.add_column("Duration", style="cyan")
        
        for i, piece in enumerate(popular[:args.popular], 1):
            duration_str = f"{piece.duration_minutes:.1f}min" if piece.duration_minutes else "Unknown"
            row = [
                str(i),
                piece.title[:40] + "..." if len(piece.title) > 40 else piece.title,
                piece.composer[:30] + "..." if len(piece.composer) > 30 else piece.composer,
                str(piece.performance_count),
                f"{piece.win_rate:.1f}%",
                f"{piece.avg_points:.1f}" if piece.avg_points else "N/A"
            ]
            
            if args.enrich_windrep:
                row.append(duration_str)
            
            table.add_row(*row)
        
        console.print(table)
    
    if args.successful:
        console.print(f"\n[bold]🏆 Top {args.successful} Most Successful Pieces[/bold]")
        successful = analyzer.get_highest_success_pieces(args.min_performances)
        
        table = Table()
        table.add_column("Rank", style="cyan")
        table.add_column("Piece", style="green")
        table.add_column("Composer", style="blue")
        table.add_column("Win Rate %", style="red")
        table.add_column("Performances", style="magenta")
        table.add_column("Avg Points", style="yellow")
        
        for i, piece in enumerate(successful[:args.successful], 1):
            table.add_row(
                str(i),
                piece.title[:40] + "..." if len(piece.title) > 40 else piece.title,
                piece.composer[:30] + "..." if len(piece.composer) > 30 else piece.composer,
                f"{piece.win_rate:.1f}%",
                str(piece.performance_count),
                f"{piece.avg_points:.1f}" if piece.avg_points else "N/A"
            )
        
        console.print(table)


if __name__ == "__main__":
    main()
