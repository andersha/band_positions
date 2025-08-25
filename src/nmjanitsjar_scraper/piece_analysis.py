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
    avg_place: Optional[float] = None  # Average placement (1st, 2nd, etc.)
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
        
        # Special case mappings for known cross-language titles
        special_cases = {
            "El Jardin de Las Herspérides": "Garden of the Hesperides",
            "Jardin de Las Herspérides": "Garden of the Hesperides",
            "El Jardín de las Hespérides": "Garden of the Hesperides",
            "Jardín de las Hespérides": "Garden of the Hesperides",
        }
        
        # Check for special case first
        if title in special_cases:
            english_title = special_cases[title]
            result = self._search_with_term(english_title, title, composer)
            if result:
                self.cache[cache_key] = result
                self._save_cache()
                return result
        
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
        
        # Strategy 3: Cross-language title variations
        alternative_titles = self._generate_alternative_titles(title)
        terms.extend(alternative_titles)
        if composer:
            for alt_title in alternative_titles:
                terms.append(f"{alt_title} {clean_composer}")
                terms.append(f"{clean_composer} {alt_title}")
        
        # Strategy 4: First significant words only (for long titles)
        title_words = clean_title.split()
        if len(title_words) > 3:
            short_title = ' '.join(title_words[:3])
            terms.append(short_title)
            if composer:
                terms.append(f"{short_title} {clean_composer}")
        
        # Strategy 5: Remove common wind band suffixes/prefixes
        simplified = re.sub(r'\b(suite|overture|march|fanfare|variations?)\b', '', clean_title, flags=re.IGNORECASE).strip()
        if simplified != clean_title and simplified:
            terms.append(simplified)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term and term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    def _generate_alternative_titles(self, title: str) -> List[str]:
        """Generate alternative titles for cross-language and variant matching."""
        alternatives = []
        title_lower = title.lower()
        
        # Spanish to English translations for common pieces (with proper capitalization for WindRep)
        spanish_english = {
            "el jardin de las hesperides": "Garden of the Hesperides",
            "jardin de las hesperides": "Garden of the Hesperides",
            "jardín de las hespérides": "Garden of the Hesperides",  # with accent
            "el jardín de las hespérides": "Garden of the Hesperides",  # with accent
            # Handle the typo in the database (Herspérides vs Hesperides)
            "el jardin de las hersperides": "Garden of the Hesperides",
            "jardin de las hersperides": "Garden of the Hesperides",
            "el jardin de las herspérides": "Garden of the Hesperides",
            "jardin de las herspérides": "Garden of the Hesperides",
        }
        
        # English to Spanish translations 
        english_spanish = {
            "garden of the hesperides": "el jardin de las hesperides",
            "garden of hesperides": "jardin de las hesperides",
        }
        
        # Normalize title for lookup (remove accents, normalize case)
        normalized_title = self._normalize_title(title_lower)
        
        # Try Spanish to English
        if normalized_title in spanish_english:
            alternatives.append(spanish_english[normalized_title])
        
        # Try English to Spanish  
        if normalized_title in english_spanish:
            alternatives.append(english_spanish[normalized_title])
        
        # Add variant with/without accents
        if "é" in title or "í" in title or "ó" in title or "á" in title:
            # Remove accents
            no_accent = title.replace("é", "e").replace("í", "i").replace("ó", "o").replace("á", "a")
            alternatives.append(no_accent)
        else:
            # Try adding common Spanish accents
            with_accents = title.replace("hesperides", "hespérides").replace("jardin", "jardín")
            if with_accents != title:
                alternatives.append(with_accents)
        
        # Handle "Las" vs "las" capitalization
        if "las hesperides" in title_lower:
            alternatives.append(title.replace("las hesperides", "Las Hesperides"))
            alternatives.append(title.replace("las hesperides", "las Hespérides"))
        
        # Common word order variations
        if "garden of the hesperides" in title_lower:
            alternatives.append("Garden of Hesperides")
            alternatives.append("The Garden of the Hesperides")
        
        # Remove duplicates and clean
        clean_alternatives = []
        for alt in alternatives:
            alt_clean = re.sub(r'[^\w\s-]', '', alt).strip()
            if alt_clean and alt_clean != re.sub(r'[^\w\s-]', '', title).strip():
                clean_alternatives.append(alt_clean)
        
        return clean_alternatives
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison by removing accents and extra spaces."""
        # Remove accents
        normalized = title.replace("é", "e").replace("í", "i").replace("ó", "o").replace("á", "a")
        normalized = normalized.replace("ñ", "n").replace("ü", "u")
        
        # Normalize spacing and case
        normalized = re.sub(r'\s+', ' ', normalized.strip().lower())
        
        return normalized
    
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
            
            # Extract from structured content (like "General Info" sections)
            info.update(self._parse_structured_content(soup))
            
            # Look for composer info in meta tags and image captions
            info.update(self._extract_composer_from_meta(soup))
            
            # Look for other structured data (MediaWiki templates)
            content_text = soup.get_text()
            
            # Extract duration from various formats in the full content
            if not info.get("duration_minutes"):
                duration = self._extract_duration(content_text)
                if duration:
                    info["duration_minutes"] = duration
            
            # Look for grade/difficulty information in the content
            if not info.get("grade_level"):
                grade = self._extract_grade_level(content_text)
                if grade:
                    info["grade_level"] = grade
                    info["difficulty"] = f"Grade {grade}"
            
            # Look for composer info if not found elsewhere
            if not info.get("composer"):
                composer_match = re.search(r'(?:composer?|composed by|by)\s*:?\s*([^\n\r\.]+)', content_text, re.IGNORECASE)
                if composer_match:
                    info["composer"] = composer_match.group(1).strip()
            
            # Look for category/genre info in categories
            if not info.get("category"):
                info.update(self._extract_category_from_meta(soup))
            
            # Fallback category extraction from text
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
    
    def _parse_structured_content(self, soup) -> Dict:
        """Parse structured content like 'General Info' sections."""
        info = {}
        
        # Look for content with structured data like "Duration: 20:00"
        content_text = soup.get_text()
        
        # Extract duration from structured format like "Duration: c. 20:00"
        duration_patterns = [
            r'Duration:\s*c?\.?\s*(\d{1,2}):(\d{2})',  # "Duration: c. 20:00"
            r'Duration:\s*c?\.?\s*(\d+)\s*(?:min|minutes?)',  # "Duration: 20 minutes"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:  # MM:SS format
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    info['duration_minutes'] = minutes + seconds / 60
                elif len(match.groups()) == 1:  # Just minutes
                    info['duration_minutes'] = float(match.group(1))
                break
        
        # Extract difficulty/grade from structured format like "Difficulty: VI"
        difficulty_patterns = [
            r'Difficulty:\s*(VI|V|IV|III|II|I|[1-7])',  # "Difficulty: VI" or "Difficulty: 6"
        ]
        
        for pattern in difficulty_patterns:
            match = re.search(pattern, content_text, re.IGNORECASE)
            if match:
                difficulty_str = match.group(1).upper()
                grade_level = self._extract_grade_level(difficulty_str)
                if grade_level:
                    info['grade_level'] = grade_level
                    info['difficulty'] = f"Grade {grade_level}"
                break
        
        return info
    
    def _extract_composer_from_meta(self, soup) -> Dict:
        """Extract composer from meta tags and image captions."""
        info = {}
        
        # Try meta description first (most reliable)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            composer_name = meta_desc['content'].strip()
            # Check if it looks like a composer name (not too short, not too long, no navigation words)
            if (composer_name and len(composer_name) > 3 and len(composer_name) < 100 and
                'Categories' not in composer_name and 'Random' not in composer_name):
                info['composer'] = composer_name
                return info
        
        # Try composer links
        composer_links = soup.find_all('a', href=re.compile(r'^/[A-Z][a-z]+_[A-Z][a-z]+'))
        for link in composer_links:
            link_text = link.get_text().strip()
            # Look for links that seem like composer names (FirstName_LastName pattern)
            if (len(link_text) > 3 and len(link_text) < 100 and 
                ' ' in link_text and link_text.count(' ') <= 3 and
                'Categories' not in link_text and 'Page' not in link_text):
                info['composer'] = link_text
                return info
        
        # Try image captions (thumb captions often contain composer names)
        thumbcaptions = soup.find_all('div', class_='thumbcaption')
        for caption in thumbcaptions:
            # Get text but skip the magnify link
            magnify_link = caption.find('div', class_='magnify')
            if magnify_link:
                magnify_link.extract()  # Remove it temporarily
            
            caption_text = caption.get_text().strip()
            
            # Skip common navigation text and look for reasonable composer names
            navigation_words = ['All Categories', 'Random Page', 'Recent Changes', 'Enlarge']
            if (caption_text and len(caption_text) > 3 and len(caption_text) < 100 and
                not any(nav_word in caption_text for nav_word in navigation_words) and
                ' ' in caption_text and caption_text.count(' ') <= 3):
                info['composer'] = caption_text
                break
        
        return info
    
    def _extract_category_from_meta(self, soup) -> Dict:
        """Extract category from MediaWiki categories."""
        info = {}
        
        # Look for category links
        category_links = soup.find_all('a', href=re.compile(r'/Category:'))
        for link in category_links:
            category_text = link.get_text().strip()
            # Skip common categories, look for musical genres
            skip_categories = ['Compositions', 'Grade', 'Award Winners', 'Multi-Movement']
            if (not any(skip in category_text for skip in skip_categories) and
                any(genre in category_text.lower() for genre in 
                    ['march', 'overture', 'suite', 'symphony', 'concerto', 'variations', 'fanfare', 'rhapsody'])):
                info['category'] = category_text
                break
        
        return info


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
            "total_place": 0,
            "place_count": 0,
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
                    # Track placement (rank) for average calculation
                    if rank and rank > 0:  # Valid rank (positive integer)
                        stats["total_place"] += rank
                        stats["place_count"] += 1
                    stats["divisions"].add(division)
                    stats["years"].add(year)
        
        # Create PieceInfo objects
        piece_infos = {}
        
        for piece_key, stats in piece_stats.items():
            title, composer = piece_key.split("|", 1)
            
            win_rate = (stats["wins"] / stats["performances"]) * 100 if stats["performances"] > 0 else 0
            avg_points = stats["total_points"] / stats["point_count"] if stats["point_count"] > 0 else None
            avg_place = stats["total_place"] / stats["place_count"] if stats["place_count"] > 0 else None
            
            piece_info = PieceInfo(
                title=title,
                composer=composer,
                performance_count=stats["performances"],
                win_rate=win_rate,
                avg_points=avg_points,
                avg_place=avg_place
            )
            
            piece_infos[piece_key] = piece_info
        
        console.print(f"✓ Analyzed {len(piece_infos)} unique pieces")
        return piece_infos
    
    def get_most_popular_pieces(self, min_performances: int = 2) -> List[PieceInfo]:
        """Get pieces sorted by performance count."""
        pieces = self.analyze_piece_popularity()
        
        # Filter and sort
        popular_pieces = [
            piece for piece in pieces.values() 
            if piece.performance_count >= min_performances
        ]
        
        return sorted(popular_pieces, key=lambda p: p.performance_count, reverse=True)
    
    def get_pieces_sorted_by(self, sort_by: str = "performances", min_performances: int = 2, reverse: bool = True) -> List[PieceInfo]:
        """
        Get pieces sorted by specified criteria.
        
        Args:
            sort_by: Field to sort by ("performances", "win_rate", "avg_points")
            min_performances: Minimum performances to include
            reverse: Sort in descending order if True
            
        Returns:
            List of sorted PieceInfo objects
        """
        pieces = self.analyze_piece_popularity()
        
        # Filter pieces
        filtered_pieces = [
            piece for piece in pieces.values() 
            if piece.performance_count >= min_performances
        ]
        
        # Define sort keys
        sort_keys = {
            "performances": lambda p: p.performance_count,
            "win_rate": lambda p: p.win_rate,
            "avg_points": lambda p: p.avg_points if p.avg_points is not None else 0,
            "avg_place": lambda p: p.avg_place if p.avg_place is not None else float('inf'),  # Lower is better for placement
            "title": lambda p: p.title.lower(),
            "composer": lambda p: p.composer.lower()
        }
        
        if sort_by not in sort_keys:
            console.print(f"[red]Invalid sort option: {sort_by}. Available: {', '.join(sort_keys.keys())}[/red]")
            sort_by = "performances"
        
        return sorted(filtered_pieces, key=sort_keys[sort_by], reverse=reverse)
    
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
    parser.add_argument("--show", type=int, default=20, help="Number of pieces to show")
    parser.add_argument("--sort-by", choices=["performances", "win_rate", "avg_points", "avg_place", "title", "composer"], 
                       default="performances", help="Sort pieces by this field")
    parser.add_argument("--ascending", action="store_true", help="Sort in ascending order (default: descending)")
    parser.add_argument("--min-performances", type=int, default=2, help="Minimum performances to include")
    parser.add_argument("--no-windrep", action="store_true", help="Skip WindRep.org enrichment (default: auto-enrich)")
    parser.add_argument("--max-enrich", type=int, default=50, help="Max pieces to enrich with WindRep (default: 50)")
    
    # Legacy compatibility
    parser.add_argument("--popular", type=int, help="Show top N popular pieces (legacy, use --show --sort-by performances)")
    parser.add_argument("--successful", type=int, help="Show top N successful pieces (legacy, use --show --sort-by win_rate)")
    
    # Keep enrich-windrep as hidden legacy option (ignored, since enrichment is now default)
    parser.add_argument("--enrich-windrep", action="store_true", help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    analyzer = PieceAnalyzer()
    
    # Handle legacy options
    if args.popular:
        args.show = args.popular
        args.sort_by = "performances"
    if args.successful:
        args.show = args.successful
        args.sort_by = "win_rate"
    
    # Get pieces sorted by specified criteria
    pieces = analyzer.get_pieces_sorted_by(
        sort_by=args.sort_by,
        min_performances=args.min_performances,
        reverse=not args.ascending
    )
    
    # Enrich with WindRep data by default (unless explicitly disabled)
    if not args.no_windrep:
        pieces = analyzer.enrich_with_windrep_data(pieces, args.max_enrich)
    
    # Display results
    sort_name_map = {
        "performances": "Most Popular",
        "win_rate": "Most Successful",
        "avg_points": "Highest Scoring",
        "avg_place": "Best Average Placement",
        "title": "Alphabetical by Title",
        "composer": "Alphabetical by Composer"
    }
    
    order = "(Ascending)" if args.ascending else "(Descending)"
    sort_display = sort_name_map.get(args.sort_by, args.sort_by.title())
    
    console.print(f"\n[bold]🎵 Top {args.show} {sort_display} Pieces {order}[/bold]")
    
    # Create table - always include Duration and Grade columns
    table = Table()
    table.add_column("Rank", style="cyan")
    table.add_column("Piece", style="green")
    table.add_column("Composer", style="blue")
    table.add_column("Performances", style="magenta")
    table.add_column("Win Rate %", style="red")
    table.add_column("Avg Points", style="yellow")
    table.add_column("Avg Place", style="bright_green")
    table.add_column("Duration", style="cyan")
    table.add_column("Grade", style="bright_red")
    
    # Add rows - always include duration and grade info
    for i, piece in enumerate(pieces[:args.show], 1):
        duration_str = f"{piece.duration_minutes:.1f}min" if piece.duration_minutes else "Unknown"
        grade_str = f"Grade {piece.grade_level}" if piece.grade_level else "Unknown"
        avg_place_str = f"{piece.avg_place:.1f}" if piece.avg_place else "N/A"
        row = [
            str(i),
            piece.title[:40] + "..." if len(piece.title) > 40 else piece.title,
            piece.composer[:30] + "..." if len(piece.composer) > 30 else piece.composer,
            str(piece.performance_count),
            f"{piece.win_rate:.1f}%",
            f"{piece.avg_points:.1f}" if piece.avg_points else "N/A",
            avg_place_str,
            duration_str,
            grade_str
        ]
        
        table.add_row(*row)
    
    console.print(table)


if __name__ == "__main__":
    main()
