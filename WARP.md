# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

# Norwegian Wind Band Orchestra Competition Data Scraper

🎺 A comprehensive data scraping and analytics application for Norwegian Wind Band Orchestra competition results from 1981-2025.

This document provides WARP with essential information about project structure, common workflows, and key architectural patterns needed to develop effectively in this codebase.

## Essential Commands

### ⚡ Setup & Dependencies
```bash
# Python 3.10+ required
poetry install
# Or with pip
pip install -r requirements.txt
```

### ⚡ Core Data Pipeline
```bash
# Run complete pipeline for all years
poetry run python -m src.nmjanitsjar_scraper.cli pipeline

# Process specific years only
poetry run python -m src.nmjanitsjar_scraper.cli pipeline --years 2024 2025

# Force refresh all cached data
poetry run python -m src.nmjanitsjar_scraper.cli pipeline --force-refresh
```

### ⚡ Individual Pipeline Stages
```bash
# Discover/verify yearly result URLs
poetry run python -m src.nmjanitsjar_scraper.cli urls --show

# Parse competition data for specific year
poetry run python -m src.nmjanitsjar_scraper.cli parse --year 2024

# Export data to CSV/JSON
poetry run python -m src.nmjanitsjar_scraper.cli export --all

# View analytics and statistics
poetry run python -m src.nmjanitsjar_scraper.cli stats --summary --top-orchestras 10
```

### ⚡ Analysis & Development
```bash
# Quick analysis with visualizations
python quick_analysis.py

# Launch Jupyter for detailed analysis
poetry run jupyter notebook notebooks/competition_analysis.ipynb
```

### ⚡ Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/

# Run tests
pytest
pytest --cov=src/nmjanitsjar_scraper
```

## High-level Architecture

The application follows a modular 4-stage pipeline architecture:

```
URLDiscovery → JSONParser → DataExporter → Analytics
     ↓             ↓            ↓           ↓
  (URLs)      (Raw JSON)   (CSV/JSON)  (Reports)
```

### Core Components

1. **URLDiscovery** (`url_discovery.py`): Discovers and verifies yearly competition result URLs
2. **JSONParser** (`parser.py`): Fetches and parses JSON data from nmjanitsjar.no APIs  
3. **DataExporter** (`exporter.py`): Normalizes and exports data to CSV/JSON formats
4. **Analytics** (`analytics.py`): Provides statistical analysis and reporting
5. **CLI** (`cli.py`): Unified command-line interface for all operations
6. **Models** (`models.py`): Pydantic data models with validation
7. **HTMLFetcher** (`fetcher.py`): Legacy HTML scraping (mostly deprecated)

### Data Flow

```
nmjanitsjar.no → JSON APIs → Pydantic Models → Normalized CSV/JSON → Analytics
     ↓              ↓              ↓                ↓               ↓
  HEAD reqs     Clean JSON    Validation       Export files    Statistics
```

## Data Pipeline & Caching Strategy

### Pipeline Stages
1. **URL Discovery**: HEAD requests to verify yearly result pages exist
2. **JSON Fetching**: Downloads from JSON APIs (`konkurranser.json`, `korps.json`, `dirigenter.json`, `musikkstykker.json`)
3. **Data Cleaning**: Removes JavaScript variable declarations from JSON responses
4. **Pydantic Validation**: Validates and structures data using type-safe models
5. **Normalization**: Creates unique IDs, splits composer/piece info, handles missing data
6. **Export**: Generates CSV files and complete JSON exports per year

### Caching Locations
- `data/json/`: Raw JSON API responses (cleaned)
- `data/processed/`: Final CSV and JSON exports
- `meta/yearly_urls.json`: Discovered URL cache

### Rate Limiting & Respectful Scraping
- 1 second delay between requests
- Checks robots.txt compliance
- Uses proper User-Agent identification
- Intelligent caching to avoid redundant requests

## Key Technical Details

### Core Pydantic Models
```python path=null start=null
class Placement(BaseModel):
    rank: int
    orchestra: str
    pieces: List[str]
    points: Optional[float]  # Validated 0-100 range
    conductor: Optional[str]
    # ... with automatic name normalization

class Division(BaseModel):
    name: str  # Elite, 1. divisjon, etc.
    placements: List[Placement]
    awards: List[Award]

class CompetitionYear(BaseModel):
    year: int  # Validated 1981-2030 range
    divisions: List[Division]
    total_orchestras: Optional[int]
```

### CLI Implementation
Uses `argparse` with subcommands for modular functionality:
- `pipeline`: Complete workflow
- `urls`: URL discovery and verification
- `parse`: JSON parsing for specific years
- `export`: Data export to various formats
- `stats`: Analytics and reporting

### Resilience Features
- **Tenacity**: Automatic retries for HTTP failures
- **Caching**: Avoids redundant API calls
- **Graceful Degradation**: Handles missing years/data
- **Data Validation**: Pydantic ensures data integrity

### Data Normalization Logic
- **Unique IDs**: Generated as `{year}-{division}-{rank:02d}-{orchestra}`
- **Composer Extraction**: Splits "Piece – Composer" format automatically
- **Name Standardization**: Normalizes orchestra and conductor names
- **Missing Data Handling**: Preserves partial records with null values

## Project Structure

```
nmjanitsjar/
├── src/nmjanitsjar_scraper/    # Main Python package
│   ├── models.py               # Pydantic data models (core business logic)
│   ├── url_discovery.py        # URL discovery and caching
│   ├── parser.py               # JSON API parsing and data extraction
│   ├── exporter.py             # CSV/JSON export with normalization
│   ├── analytics.py            # Statistical analysis and reporting
│   ├── cli.py                  # Command-line interface (main entry point)
│   └── fetcher.py              # Legacy HTML scraping (deprecated)
├── data/
│   ├── json/                   # Cached JSON API responses
│   ├── processed/              # Final CSV/JSON exports (per year)
│   └── raw/                    # Legacy HTML cache (unused)
├── meta/                       # Metadata and configuration
│   └── yearly_urls.json        # Discovered URL cache
├── notebooks/                  # Jupyter analysis notebooks
│   └── competition_analysis.ipynb  # Comprehensive data analysis
├── tests/                      # Unit tests (currently empty - needs implementation)
├── quick_analysis.py           # Standalone visualization script
└── pyproject.toml              # Poetry configuration and dependencies
```

## Common Development Tasks & Recipes

### Add Support for New JSON Field
1. Update Pydantic models in `models.py`
2. Modify parser logic in `parser.py` 
3. Update exporter normalization in `exporter.py`
4. Add tests for new field validation

### Scrape Newly Finished Competition Year
```bash
# For new year (e.g., 2026)
poetry run python -m src.nmjanitsjar_scraper.cli pipeline --years 2026

# Check if URL exists first
poetry run python -m src.nmjanitsjar_scraper.cli urls --show
```

### Debug a Failing Year
```bash
# Parse specific year to see error details
poetry run python -m src.nmjanitsjar_scraper.cli parse --year 2024

# Check cached JSON for data issues
ls data/json/
cat data/json/konkurranser.json | jq '.konkurranser[] | select(.aarstall == 2024)'
```

### Clear Cache and Force Refresh
```bash
# Clear all cached data
rm -rf data/json/* data/processed/* meta/yearly_urls.json

# Force complete refresh
poetry run python -m src.nmjanitsjar_scraper.cli pipeline --force-refresh
```

### Generate Quick Analysis Report
```bash
# Run standalone analysis with plots
python quick_analysis.py

# Open Jupyter for detailed analysis
poetry run jupyter notebook notebooks/competition_analysis.ipynb
```

### Export Statistics and Reports
```bash
# Comprehensive statistics
poetry run python -m src.nmjanitsjar_scraper.cli stats --summary --divisions --years

# Top performers analysis
poetry run python -m src.nmjanitsjar_scraper.cli stats --top-orchestras 20 --conductors 15
```

## Data Schema Reference

### CSV Export Structure
- **Placements**: `{year}_placements.csv` with columns: id, year, division, rank, orchestra, conductor, pieces, composers, points, max_points, image_url, scraped_at
- **Awards**: `{year}_awards.csv` with columns: id, year, division, award_type, recipient, orchestra, scraped_at
- **Combined**: `{year}_complete.json` with full structured data including metadata

### JSON API Endpoints
- `konkurranser.json`: Competition entries and results
- `korps.json`: Orchestra information and metadata
- `dirigenter.json`: Conductor information
- `musikkstykker.json`: Musical pieces database
- `repmus.json`: Repertoire assignments (optional)

## Dependencies & Tech Stack

### Core Dependencies
- **Pydantic**: Data validation and serialization
- **Requests**: HTTP client with session management
- **Rich**: Beautiful terminal output and progress bars
- **Pandas**: Data manipulation and CSV export
- **Tenacity**: Robust retry logic for HTTP requests

### Development Dependencies
- **pytest**: Unit testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Code linting
- **jupyter**: Interactive analysis notebooks

### Analysis Stack
- **matplotlib/seaborn**: Statistical plotting
- **plotly**: Interactive visualizations
- **numpy**: Numerical computing support

## Performance Characteristics

- **Processing Speed**: Handles 40+ years of data in under 2 minutes
- **Export Performance**: 1000+ records to CSV in seconds
- **Memory Efficiency**: Streaming approach for large datasets
- **Incremental Updates**: Only processes new/changed data when possible
- **Cache Efficiency**: Avoids redundant HTTP requests through intelligent caching
