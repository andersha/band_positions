# Norwegian Brass Band Competition Data Scraper

This extension to the nmjanitsjar project adds support for scraping and exporting Norwegian brass band competition data from [nmbrass.no](https://nmbrass.no).

## Overview

The brass band scraper follows the same architecture as the existing wind band scraper but handles XML data instead of JSON. It fetches competition results from 2001-2025 (23 years of data) covering 125 orchestras, 285 conductors, and 414 repertoire pieces.

## Key Differences from Wind Band Scraper

| Feature | Wind Bands (nmjanitsjar.no) | Brass Bands (nmbrass.no) |
|---------|---------------------------|-------------------------|
| Data Format | JSON | XML |
| Data Source | `https://nmbrass.no/nmjanitsjar/*.json` | `https://nmbrass.no/*.xml` |
| Years Available | 1981-2025 (41 years) | 2001-2025 (23 years) |
| Repertoire Structure | Separate link table (`repmus.json`) | Direct piece mapping (`repertoar.xml`) |
| Character Encoding | UTF-8 | windows-1252, iso-8859-1, utf-8 (mixed) |

## Installation

The brass band scraper uses the same dependencies as the wind band scraper:

```bash
# All dependencies are already installed if you've set up the wind band scraper
poetry install
```

## Usage

### Quick Start - Export All Data

```bash
# Export all brass band data
python3 export_brass.py

# Force refresh cached XML data
python3 export_brass.py --force-refresh

# Export specific year only
python3 export_brass.py --year 2025

# Export multiple years
python3 export_brass.py --years 2023 2024 2025
```

### Using the Brass Parser Directly

```python
from pathlib import Path
from src.nmjanitsjar_scraper.brass_parser import BrassXMLParser
from src.nmjanitsjar_scraper.exporter import DataExporter

# Initialize parser
parser = BrassXMLParser()
parser.load_all_data()

# Get available years
years = parser.get_available_years()
print(f"Available years: {years}")

# Parse specific year
competition_data = parser.parse_year(2025)
print(f"2025: {competition_data.total_orchestras} orchestras")

# Export data
exporter = DataExporter(
    output_dir=Path("data/brass/processed"),
    parser=parser
)
result = exporter.export_all_years()
```

### Command Line Interface

```bash
# Show all available years
python -m src.nmjanitsjar_scraper.brass_parser --all-years

# Parse specific year
python -m src.nmjanitsjar_scraper.brass_parser --year 2025

# Force refresh cached data
python -m src.nmjanitsjar_scraper.brass_parser --all-years --force-refresh
```

## Data Structure

### Output Files

The scraper generates the same file structure as the wind band scraper:

```
data/brass/
├── xml/                          # Cached XML files from nmbrass.no
│   ├── konkurranser.xml
│   ├── korps.xml
│   ├── dirigenter.xml
│   └── repertoar.xml
└── processed/                    # Exported data files
    ├── all_placements.csv        # Master CSV with all placements
    ├── all_data.json             # Master JSON summary
    ├── all_placements_records.json
    ├── 2025_placements.csv       # Per-year CSV files
    ├── 2025_complete.json        # Per-year JSON files
    └── ...
```

### CSV Schema

The output CSV files use the same schema as wind band data, ensuring compatibility:

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique placement identifier |
| year | int | Competition year |
| division | string | Division name (Elite, 1. divisjon, etc.) |
| rank | int | Placement rank within division |
| orchestra | string | Orchestra name |
| conductor | string | Conductor name |
| pieces | string | Semicolon-separated list of pieces |
| composers | string | Semicolon-separated list of composers |
| points | float | Total points scored |
| max_points | float | Maximum possible points (100.0) |
| image_url | string | Orchestra image URL (if available) |
| scraped_at | datetime | Timestamp when data was scraped |

## Technical Details

### XML Parsing

The brass band data uses XML format with multiple character encodings:

```python
# The parser handles multiple encodings automatically
encodings_tried = ['utf-8', 'windows-1252', 'iso-8859-1']
```

**Note:** Some orchestra and conductor names contain Norwegian characters (æ, ø, å) that may not display correctly in all editors. The data is correctly encoded in UTF-8 for export.

### Data Models

The brass parser reuses the same Pydantic models as the wind band scraper:

- `CompetitionYear`: Complete year's results
- `Division`: Single division with placements
- `Placement`: Individual orchestra placement
- `Award`: Special awards (currently not available in XML)

### Architecture

```
BrassXMLParser (brass_parser.py)
    ↓
Uses same models (models.py)
    ↓
Feeds into DataExporter (exporter.py)
    ↓
Outputs same CSV/JSON format
```

## Limitations & Known Issues

1. **Awards Data**: The XML format from nmbrass.no doesn't include awards data (best soloist, best group), so all awards files are empty.

2. **Character Encoding**: Some orchestra names may display with encoding artifacts (e.g., "Bjørsvik" → "Bj�rsvik") in certain contexts. The data is correctly stored as UTF-8.

3. **Missing Years**: Competition data is only available from 2001 onwards. Years 2021 and 2022 are missing (likely due to COVID-19).

4. **Repertoire Differences**: Unlike wind bands, brass bands have a simpler repertoire structure with direct piece mappings rather than separate linking tables.

## Integration with Frontend App

The exported brass band data uses the same schema as wind band data, allowing for easy integration:

```bash
# Copy brass band data to the frontend app
cp data/brass/processed/all_placements.csv apps/band-positions/public/data/brass_placements.csv
cp data/brass/processed/all_data.json apps/band-positions/public/data/brass_data.json
```

The frontend can then load both datasets and allow users to toggle between wind and brass bands.

## Data Quality

The scraper includes several data quality features:

- ✅ Validates year ranges (2001-2025)
- ✅ Normalizes division names
- ✅ Handles missing/malformed data gracefully
- ✅ Logs warnings for parsing errors
- ✅ Deduplicates orchestras and conductors
- ✅ Links repertoire to composers

## Statistics

Current brass band dataset (as of 2025):

- **Years covered**: 23 (2001-2025)
- **Total placements**: 1,628
- **Unique orchestras**: 125
- **Unique conductors**: 285
- **Repertoire pieces**: 414
- **Divisions**: Elite through 6th division

## Comparison: Wind vs Brass Bands

| Metric | Wind Bands | Brass Bands |
|--------|-----------|-------------|
| Years | 41 (1981-2025) | 23 (2001-2025) |
| Total Placements | ~1,000+ | 1,628 |
| Data Format | JSON | XML |
| Divisions | Elite + 1-7 | Elite + 1-6 |

## Future Enhancements

- [ ] Add CLI flag to main `cli.py` for `--brass` mode
- [ ] Merge wind and brass data into unified database schema
- [ ] Add analytics specifically for brass bands
- [ ] Implement differential updates (only fetch new years)
- [ ] Add data validation tests
- [ ] Create visualization comparing wind vs brass competitions

## Contributing

To add new features to the brass band scraper:

1. Follow the same patterns as `parser.py` (JSON parser)
2. Maintain compatibility with existing `models.py`
3. Ensure output format matches wind band schema
4. Add tests for new functionality
5. Update this README with changes

## License

Same as the main nmjanitsjar project - intended for educational and research purposes.

---

**Questions or Issues?** Check the main project README or contact the maintainer.