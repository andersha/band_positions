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
    grade_level: Optional[int] = None  # Numeric grade 1-7
    category: Optional[str] = None
    windrep_url: Optional[str] = None
    performance_count: int = 0
    win_rate: float = 0.0
    avg_points: Optional[float] = None
    is_set_test_piece: bool = False  # Flag for mandatory pieces


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
    
    def __init__(self, cache_file: Path = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Norwegian Band Competition Analyzer/1.0 (Research Project)'
        })
        self.cache_file = cache_file or Path("data/windrep_cache.json")
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]Failed to load WindRep cache: {e}[/yellow]")
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]Failed to save WindRep cache: {e}[/yellow]")
        
    def search_piece(self, title: str, composer: str = None) -> Optional[Dict]:
        """
        Search for a piece on WindRep.org with multiple search strategies.
        
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
        
        # Try multiple search strategies
        search_terms = self._generate_search_terms(title, composer)
        
        for search_term in search_terms:
            result = self._search_with_term(search_term, title, composer)
            if result:
                self.cache[cache_key] = result
                self._save_cache()
                return result
                
            # Rate limiting between searches
            time.sleep(0.5)
        
        # No results found
        self.cache[cache_key] = None
        self._save_cache()
        return None
    
    def _generate_search_terms(self, title: str, composer: str = None) -> List[str]:
        """Generate multiple search terms to try."""
        terms = []
        
        # Clean title for search
        clean_title = re.sub(r'[^\w\s-]', '', title).strip()
        
        # Strategy 1: Full title
        terms.append(clean_title)
        
        # Strategy 2: Title with composer
        if composer:
            clean_composer = re.sub(r'[^\w\s-]', '', composer).strip()
            # Remove "arr." prefixes from composer
            clean_composer = re.sub(r'^arr\.?\s+', '', clean_composer, flags=re.IGNORECASE)
            terms.append(f"{clean_title} {clean_composer}")
            terms.append(f"{clean_composer} {clean_title}")
        
        # Strategy 3: First significant words only (for long titles)
        title_words = clean_title.split()
        if len(title_words) > 3:
            short_title = ' '.join(title_words[:3])
            terms.append(short_title)
            if composer:
                terms.append(f"{short_title} {clean_composer}")
        
        # Strategy 4: Remove common wind band suffixes/prefixes
        simplified = re.sub(r'\b(suite|overture|march|fanfare|variations?)\b', '', clean_title, flags=re.IGNORECASE).strip()
        if simplified != clean_title and simplified:
            terms.append(simplified)
        
        return terms
    
    def _search_with_term(self, search_term: str, original_title: str, composer: str = None) -> Optional[Dict]:
        """Search with a specific term."""
        try:
            # Use MediaWiki search API
            search_params = {
                'action': 'opensearch',
                'search': search_term,
                'limit': 15,  # Increased limit
                'namespace': 0,
                'format': 'json'
            }
            
            search_url = f"{self.BASE_URL}/api.php"
            response = self.session.get(search_url, params=search_params, timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                if len(results) >= 2 and results[1]:  # results[1] contains titles
                    # Look for best match
                    for i, result_title in enumerate(results[1]):
                        if self._is_good_match(original_title, result_title, composer):
                            page_url = results[3][i] if len(results) > 3 else f"{self.BASE_URL}/wiki/{result_title.replace(' ', '_')}"
                            return self._extract_piece_info(page_url, result_title)
            
        except Exception as e:
            console.print(f"[yellow]WindRep search failed for '{search_term}': {e}[/yellow]")
        
        return None
    
    def _is_good_match(self, search_title: str, result_title: str, composer: str = None) -> bool:
        """Check if a search result is a good match for the piece."""
        # Normalize strings for comparison
        search_clean = re.sub(r'[^\w\s]', '', search_title.lower()).strip()
        result_clean = re.sub(r'[^\w\s]', '', result_title.lower()).strip()
        
        # Exact match
        if search_clean == result_clean:
            return True
        
        # Check title similarity - substring match
        if search_clean in result_clean or result_clean in search_clean:
            return True
        
        # Check for partial matches with word overlap
        search_words = set(word for word in search_clean.split() if len(word) > 2)  # Ignore short words
        result_words = set(word for word in result_clean.split() if len(word) > 2)
        
        if not search_words or not result_words:
            return False
        
        # Calculate overlap percentage
        overlap = len(search_words.intersection(result_words))
        overlap_ratio = overlap / min(len(search_words), len(result_words))
        
        # Good match if significant word overlap
        if overlap >= 2 and overlap_ratio >= 0.6:
            return True
        
        # Special case: check if composer is mentioned in the result title
        if composer:
            composer_clean = re.sub(r'[^\w\s]', '', composer.lower())
            composer_words = set(word for word in composer_clean.split() if len(word) > 2)
            
            # If composer words appear in result and some title words match
            if composer_words.intersection(result_words) and overlap >= 1:
                return True
        
        return False
    
    def _extract_piece_info(self, page_url: str, title: str) -> Dict:
        """Extract piece information from WindRep page."""
        try:
            response = self.session.get(page_url, timeout=15)
            if response.status_code != 200:
                return {"title": title, "url": page_url}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            info = {
                "title": title,
                "url": page_url,
                "composer": None,
                "duration_minutes": None,
                "difficulty": None,
                "grade_level": None,
                "category": None
            }
            
            # Look for infobox or structured data
            infobox = soup.find('table', class_='infobox') or soup.find('div', class_='infobox')
            if infobox:
                info.update(self._parse_infobox(infobox))
            
            # Look for other structured data (MediaWiki templates)
            content_text = soup.get_text()
            
            # Extract duration from various formats in the full content
            duration = self._extract_duration(content_text)
            if duration and not info.get("duration_minutes"):
                info["duration_minutes"] = duration
            
            # Look for grade/difficulty information in the content
            if not info.get("grade_level"):
                grade = self._extract_grade_level(content_text)
                if grade:
                    info["grade_level"] = grade
                    info["difficulty"] = f"Grade {grade}"
            
            # Look for composer info if not found in infobox
            if not info.get("composer"):
                composer_match = re.search(r'(?:composer?|composed by|by)\s*:?\s*([^\n\r\.]+)', content_text, re.IGNORECASE)
                if composer_match:
                    info["composer"] = composer_match.group(1).strip()
            
            # Look for category/genre info
            if not info.get("category"):
                category_patterns = [
                    r'(?:category|genre|type)\s*:?\s*([^\n\r\.]+)',
                    r'\b(march|overture|suite|symphony|concerto|variations?|fanfare|rhapsody)\b'
                ]
                for pattern in category_patterns:
                    match = re.search(pattern, content_text, re.IGNORECASE)
                    if match:
                        info["category"] = match.group(1).strip().title()
                        break
            
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
                    # Store original difficulty value
                    info['difficulty'] = value
                    # Also extract numeric grade if possible
                    grade_level = self._extract_grade_level(value)
                    if grade_level:
                        info['grade_level'] = grade_level
                elif 'genre' in key or 'category' in key:
                    info['category'] = value
        
        return info
    
    def _extract_grade_level(self, text: str) -> Optional[int]:
        """Extract numeric grade level from text, including Roman numerals."""
        # Try to find Roman numerals (I through VII)
        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7}
        roman_pattern = r'\b(VII|VI|V|IV|III|II|I)\b'
        
        # Also look for numeric grades like "Grade 5" or "Grade: 4"
        numeric_pattern = r'(?:grade|level)[\s:]*([1-7])'
        
        # Check for Roman numerals first
        roman_match = re.search(roman_pattern, text, re.IGNORECASE)
        if roman_match:
            roman = roman_match.group(1).upper()
            return roman_map.get(roman)
        
        # Then check for numeric representation
        numeric_match = re.search(numeric_pattern, text, re.IGNORECASE)
        if numeric_match:
            try:
                return int(numeric_match.group(1))
            except (ValueError, TypeError):
                pass
        
        # Finally check for standalone numbers if it looks like a grade
        # (only if the text is short, to avoid false positives)
        if len(text) < 5 and text.strip().isdigit() and 1 <= int(text.strip()) <= 7:
            return int(text.strip())
            
        return None
    
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
    
    def enrich_with_windrep_data(self, pieces: List[PieceInfo], max_pieces: int = 200) -> List[PieceInfo]:
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
        successful_lookups = 0
        
        for piece in track(pieces[:max_pieces], description="Fetching piece details..."):
            windrep_info = self.windrep.search_piece(piece.title, piece.composer)
            
            if windrep_info:
                # Update piece with WindRep data
                piece.duration_minutes = windrep_info.get("duration_minutes") or piece.duration_minutes
                piece.difficulty = windrep_info.get("difficulty") or piece.difficulty
                piece.grade_level = windrep_info.get("grade_level") or piece.grade_level
                piece.category = windrep_info.get("category") or piece.category
                piece.windrep_url = windrep_info.get("url")
                
                # Count successful lookups (ones that returned actual data)
                if any([windrep_info.get("duration_minutes"), windrep_info.get("difficulty"), 
                       windrep_info.get("grade_level"), windrep_info.get("category")]):
                    successful_lookups += 1
            
            enriched_pieces.append(piece)
        
        console.print(f"✓ Enriched {len(enriched_pieces)} pieces with external data")
        console.print(f"✓ Found detailed metadata for {successful_lookups} pieces")
        return enriched_pieces
    
    def analyze_set_test_pieces(self) -> Dict[str, List[Dict]]:
        """
        Analyze pieces that might have been set test pieces (mandatory).
        
        Set test pieces often show unusual patterns:
        - High performance count in specific years
        - Similar performance across different divisions in the same year
        - Concentrated in single years rather than spread over time
        
        Returns:
            Dictionary with suspected set test pieces by division and year
        """
        console.print("[blue]Analyzing potential set test pieces...[/blue]")
        
        # Load all data
        self.parser.load_all_data()
        
        # Build repertoire to piece mapping
        repertoire_to_piece = {}
        for item in self.parser._repmus.get("repmus", []):
            rep_nr = item.get("repertoarnr")
            piece_nr = item.get("musikkstykkenr")
            if rep_nr and piece_nr:
                repertoire_to_piece[rep_nr] = piece_nr
        
        # Get piece information
        pieces_lookup = {}
        for piece in self.parser._musikkstykker.get("musikkstykker", []):
            piece_id = piece.get("musikkstykkenr")
            if piece_id:
                pieces_lookup[piece_id] = {
                    "title": piece.get("tittel", "Unknown"),
                    "composer": piece.get("komponist", "Unknown")
                }
        
        # Analyze performances by year, division, and piece
        year_division_piece_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        for comp in self.parser._konkurranser.get("konkurranser", []):
            repertoire_id = comp.get("repertoarnr")
            division = comp.get("divisjon", "Unknown")
            year = comp.get("aarstall")
            
            if repertoire_id and repertoire_id in repertoire_to_piece:
                piece_id = repertoire_to_piece[repertoire_id]
                if piece_id in pieces_lookup:
                    piece_key = f"{pieces_lookup[piece_id]['title']}|{pieces_lookup[piece_id]['composer']}"
                    year_division_piece_counts[year][division][piece_key] += 1
        
        # Look for suspicious patterns
        suspected_set_pieces = defaultdict(list)
        
        for year, divisions in year_division_piece_counts.items():
            for division, pieces in divisions.items():
                # Look for pieces with unusually high performance counts
                # A piece performed by more than 60% of orchestras in a division/year is suspicious
                total_performances = sum(pieces.values())
                avg_per_piece = total_performances / len(pieces) if pieces else 0
                
                for piece_key, count in pieces.items():
                    # Criteria for suspected set piece:
                    # 1. More than 5 performances in one year/division
                    # 2. Or more than 3x the average for that division/year
                    if count >= 5 or (avg_per_piece > 0 and count >= avg_per_piece * 3):
                        title, composer = piece_key.split("|", 1)
                        suspected_set_pieces[f"{year}_{division}"].append({
                            "year": year,
                            "division": division,
                            "title": title,
                            "composer": composer,
                            "performances": count,
                            "total_in_division": total_performances,
                            "percentage_of_division": (count / total_performances) * 100 if total_performances > 0 else 0
                        })
        
        console.print(f"✓ Identified {sum(len(v) for v in suspected_set_pieces.values())} potential set test pieces")
        return dict(suspected_set_pieces)
    
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
            table.add_column("Grade", style="bright_red")
        
        for i, piece in enumerate(popular[:args.popular], 1):
            duration_str = f"{piece.duration_minutes:.1f}min" if piece.duration_minutes else "Unknown"
            grade_str = f"Grade {piece.grade_level}" if piece.grade_level else "Unknown"
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
                row.append(grade_str)
            
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
