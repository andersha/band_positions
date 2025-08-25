# 🎵 Norwegian Wind Band Competition - Piece Analysis Notebook

This interactive Jupyter notebook provides comprehensive analysis and visualization of musical pieces from 40+ years of Norwegian Wind Band competitions.

## 🚀 Quick Start

### Method 1: Use the Launcher Script
```bash
# From the project root directory
python run_piece_analysis_notebook.py
```

### Method 2: Manual Launch  
```bash
# Install requirements
pip install jupyter matplotlib seaborn numpy pandas

# Launch Jupyter
jupyter notebook
# Navigate to notebooks/piece_analysis.ipynb
```

## 📊 What's Inside

### 1. Data Overview
- **911 unique pieces** analyzed from competition database
- **2,338 total performances** tracked across decades  
- **40 suspected mandatory pieces** identified
- **WindRep.org integration** for piece metadata

### 2. Interactive Visualizations

**📈 Performance Analysis**
- Performance count distributions
- Win rate vs popularity correlations
- Success rate patterns and trends

**🎼 Composer Insights** 
- Most performed composers by total performances
- Success rates across composer catalogs
- Productivity vs. success analysis

**🎯 Set Test Piece Detection**
- Timeline of mandatory pieces (2000-2004)
- Statistical anomaly detection (100% performance rates)
- Division-specific mandatory piece patterns

**⏱️ Duration & Constraints**
- Division time limit analysis (15-35 minutes)
- Piece-division compatibility matrices
- Program optimization insights

**🌐 WindRep.org Enrichment**
- Grade level distribution (I-VII scale)
- Duration data integration
- Difficulty assessment patterns

### 3. Key Findings

**Most Popular Pieces:**
- "Puszta (Four Gypsi Dances)" - 32 performances
- "Incantation and Dance" - 24 performances (7.8 min)
- "Armenian Dances, Part 1" - 23 performances (17.4% win rate)

**Confirmed Set Test Pieces:**
- 2004: "Heroes, Lost and Fallen" (1st Division - 100% performance rate)
- 2003: "Puszta" (2nd Division - 100% performance rate)  
- 2001: "Blue Shades" (1st Division - 100% performance rate)

**Duration Insights:**
- Average piece duration: ~10-12 minutes
- Many pieces exceed lower division limits (15 min)
- Elite/1st Division pieces can utilize full 25-35 minute limits

## 📁 Exports

The notebook automatically exports analysis results to CSV files:

- `popular_pieces_analysis.csv` - Top performing pieces by frequency
- `successful_pieces_analysis.csv` - Highest win rate pieces  
- `enriched_pieces_analysis.csv` - WindRep.org enhanced metadata
- `set_test_pieces_analysis.csv` - Suspected mandatory pieces
- `composer_analysis.csv` - Composer performance statistics

## 🔧 Technical Features

**Data Processing:**
- Robust piece-repertoire mapping via `repmus` linkage
- Statistical anomaly detection for set pieces
- Grade level parsing with Roman numeral support

**Visualizations:**
- Interactive matplotlib/seaborn charts
- Heatmaps for constraint compatibility
- Distribution analysis with statistical overlays

**Export Capabilities:**
- Multi-format data exports (CSV/JSON)
- Timestamped analysis snapshots
- Research-ready datasets

## 🎯 Use Cases

**For Conductors:**
- Repertoire selection based on historical success
- Program planning within time constraints
- Grade-appropriate piece identification

**For Researchers:**
- Competition dynamics analysis
- Repertoire trend studies
- Statistical pattern recognition

**For Competition Organizers:**
- Set piece impact assessment
- Division difficulty calibration
- Historical precedent analysis

## 📊 Future Enhancements

- **Expanded WindRep integration** for complete duration database
- **Program optimization algorithms** using constraint satisfaction
- **Geographic analysis** by orchestra region/location
- **Temporal trend analysis** across decades
- **Recommendation engine** for orchestra-specific suggestions

---

*This notebook demonstrates the power of combining historical competition data with external metadata sources to provide actionable insights for musical program selection and performance optimization.*

## Dependencies

- `jupyter` - Interactive notebook environment
- `matplotlib` - Static plotting and visualization
- `seaborn` - Statistical data visualization  
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `src.nmjanitsjar_scraper` - Custom competition data analysis module
