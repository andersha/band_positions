# Musical Piece Popularity Analysis 🎵

This module provides comprehensive analysis of musical piece performance across 40+ years of Norwegian Wind Band Orchestra competitions, enriched with metadata from WindRep.org.

## Overview

The piece analysis system analyzes historical competition data to identify:
- **Most popular pieces** by performance frequency
- **Most successful pieces** by win rates and average scores
- **Piece metadata** including duration, difficulty, and categorization
- **Division time constraints** for program optimization

## Features

### 🔍 Data Analysis
- **911 unique pieces** analyzed from 2,338 total performances
- **Repertoire mapping** connecting competition data to piece information via `repmus` linkage
- **Performance statistics** including win rates, average points, and division breakdowns
- **Historical trends** across years and divisions

### 🌐 WindRep.org Integration
- **Automated scraping** of piece metadata from WindRep.org
- **Duration extraction** supporting multiple time formats (MM:SS, minutes, etc.)
- **Difficulty assessment** and categorization from structured data
- **Rate limiting** and caching for respectful API usage

### 📊 Division Constraints
Time limits for optimal program selection:
- **Elite Division**: 35 minutes maximum
- **1st Division**: 25 minutes maximum  
- **2nd Division**: 20 minutes maximum
- **3rd-7th Divisions**: 15 minutes maximum (3 pieces max)

### 📈 Export Formats
- **CSV exports** for spreadsheet analysis
- **JSON exports** with comprehensive metadata
- **Rich terminal output** with formatted tables
- **Timestamped files** for historical tracking

## Usage

### Command Line Interface

```bash
# Show top 15 most popular pieces (3+ performances)
python -m src.nmjanitsjar_scraper.piece_analysis --popular 15 --min-performances 3

# Show top 10 most successful pieces with WindRep enrichment
python -m src.nmjanitsjar_scraper.piece_analysis --successful 10 --enrich-windrep

# Export comprehensive analysis to files
python export_piece_analysis.py
```

### Python API

```python
from src.nmjanitsjar_scraper.piece_analysis import PieceAnalyzer

analyzer = PieceAnalyzer()

# Get all piece statistics
pieces = analyzer.analyze_piece_popularity()

# Get top performers
popular = analyzer.get_most_popular_pieces(min_performances=5)
successful = analyzer.get_highest_success_pieces(min_performances=3)

# Enrich with WindRep data
enriched = analyzer.enrich_with_windrep_data(popular[:10])
```

## Key Insights

### 🏆 Top Popular Pieces
1. **Puszta (Four Gypsi Dances)** by Jan Van der Roost - 32 performances (6.2% win rate)
2. **Incantation and Dance** by John Barnes Chance - 24 performances (12.5% win rate, ~7.8 min)
3. **Variations for Band** by John Brakstad - 24 performances (4.2% win rate)
4. **Armenian Dances, Part 1** by Alfred Reed - 23 performances (17.4% win rate)
5. **Blue Shades** by Frank Ticheli - 23 performances (13.0% win rate, 10.5 min)

### ⭐ High Success Rate Pieces
Many pieces achieve 33-50% win rates, suggesting:
- **Quality over quantity**: Less frequently performed pieces often have higher success rates
- **Strategic selection**: Orchestras may choose pieces that suit their strengths
- **Division dynamics**: Success rates vary significantly across competitive divisions

### ⏱️ Duration Analysis
Sample pieces with duration data from WindRep.org:
- **Festivo** by Edward Gregson: 2.5 minutes (perfect opener)
- **Incantation and Dance**: ~7.8 minutes (mid-length piece)
- **Blue Shades**: 10.5 minutes (substantial work)
- **Music for a Festival**: ~33.8 minutes (full program piece)

## Technical Implementation

### Data Flow
```
Competition Data → Repertoire Mapping → Piece Identification → Performance Analysis → WindRep Enrichment → Export
```

### WindRep.org Scraping
- **MediaWiki API** for piece searching
- **BeautifulSoup** for HTML parsing and metadata extraction  
- **Regex patterns** for duration parsing from multiple formats
- **Caching system** to avoid duplicate requests
- **Error handling** for missing or malformed data

### Performance Optimization
- **Efficient data structures** using defaultdict for statistics aggregation
- **Batch processing** for WindRep requests with rate limiting
- **Memory-conscious** handling of large datasets
- **Progress tracking** with rich terminal interfaces

## Data Quality

### Coverage
- **2,609 repertoire mappings** connecting competitions to pieces
- **911 unique pieces** with performance statistics
- **218 popular pieces** with 3+ performances for reliable statistics
- **11 WindRep matches** out of top 25 pieces (~44% success rate)

### Enrichment Success
- **10 pieces** with duration data successfully extracted
- **Duration formats** supported: MM:SS, minutes, seconds, mixed formats
- **Error handling** for network issues, parsing failures, and missing data

## Future Enhancements

### 🎯 Program Optimization Engine
- **Constraint satisfaction** for division time limits
- **Piece recommendation** based on historical success within time constraints
- **Combination analysis** for optimal program construction

### 📊 Advanced Analytics
- **Trend analysis** over time periods
- **Composer popularity** and success patterns  
- **Division-specific** piece performance analysis
- **Geographic patterns** in piece selection

### 🔗 Enhanced Metadata
- **IMSLP integration** for additional piece information
- **Publisher databases** for availability and difficulty ratings
- **Recording references** for performance examples
- **Custom metadata** input and management

## File Structure

```
data/piece_analysis/
├── all_pieces_YYYYMMDD_HHMMSS.csv          # Complete piece database
├── popular_pieces_YYYYMMDD_HHMMSS.csv      # Top popular pieces (enriched)
├── successful_pieces_YYYYMMDD_HHMMSS.csv   # Highest success rates
├── piece_analysis_YYYYMMDD_HHMMSS.json     # Comprehensive JSON export
└── latest/                                 # Symlinks to most recent exports
```

## Dependencies

- **requests**: HTTP client for WindRep.org API
- **beautifulsoup4**: HTML parsing and data extraction
- **rich**: Terminal formatting and progress bars
- **pandas**: Data manipulation (optional for advanced analysis)
- **pydantic**: Data validation and models

## Contributing

When adding new features:
1. **Maintain rate limiting** for external API requests
2. **Add comprehensive error handling** for network and parsing failures
3. **Include progress indicators** for long-running operations
4. **Update export formats** to include new metadata fields
5. **Add unit tests** for critical data processing functions

---

*This analysis system demonstrates the power of combining historical competition data with external metadata sources to provide actionable insights for musical program selection and performance optimization.*
