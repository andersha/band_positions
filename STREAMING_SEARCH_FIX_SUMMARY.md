# Streaming Search Fix Summary

**Date**: 2025-10-04  
**Status**: ✅ COMPLETE - All 80/80 performances matched

## Problem Statement

The streaming search script was only matching 72 out of 80 performances for the 2025 brass band competition. The script was making excessive API calls and matching tracks from incorrect years (2019, 2023) instead of 2025 albums.

## Root Causes Identified

1. **Early Break Bug**: Script had `if tracks: break` statements that stopped searching after finding the first album with any tracks, even if it was from the wrong year/division
2. **No Year Filtering**: Script collected tracks from albums across all years, then filtered them out at the end, causing mismatches
3. **Poor Album Prioritization**: Older albums were sometimes processed before 2025 albums due to lack of relevance scoring
4. **Excessive API Calls**: Script was trying hundreds of search term variants, causing rate limiting

## Solutions Implemented

### 1. Removed Early Break Logic
**File**: `src/nmjanitsjar_scraper/streaming_search.py`  
**Lines**: 495-496 (Spotify), 570-571 (Apple Music)

- Removed `if tracks: break` statements
- Now processes ALL search terms and collects all relevant albums before filtering

### 2. Added Album Relevance Scoring
**Function**: `score_album_relevance()` (lines 146-194)

Scoring system prioritizes:
- **+200 points**: Release year matches target year
- **+100 points**: Year appears in album name
- **+150 points**: Division tokens match (e.g., "1. div", "Elitedivisjon")
- **+20 points**: Contest tokens present ("NM Brass", "Norgesmesterskap")
- **+5 points**: Live recording indicator
- **+2/-10 points**: Album type (prefer albums over singles)

### 3. Added Division Token Helper
**Function**: `get_division_tokens()` (lines 119-143)

Generates normalized tokens for division matching:
- Elite → ["elite", "elitedivisjon", "elite-divisjon", "elite divisjon"]
- 1. divisjon → ["1. div", "1 div", "1. divisjon", "1-divisjon", "1.div", "1div"]
- Similar patterns for divisions 2-7

### 4. Strict Year Filtering
**Lines**: 592-613 (Spotify), 748-771 (Apple Music)

**Critical change**: Albums are now filtered to ONLY include albums from the target year BEFORE collecting tracks:

```python
# Only include albums from the target year
if release_year == year or str(year) in album_name_lower:
    filtered_albums.append((score, album))
```

This ensures we never look at tracks from wrong years (2019, 2023, etc.)

### 5. Graceful Error Handling
**Lines**: 411-413 (Apple Music search), 430-432 (Apple Music lookup)

Added handling for 403 Forbidden errors:
```python
if response.status_code == 403:
    print(f"[apple] 403 forbidden on search('{term}') – rate limited, skipping Apple Music")
    return []
```

Script now continues with Spotify-only results instead of crashing.

### 6. Reduced API Calls
**Lines**: 562 (Spotify), 692 (Apple Music)

Added early termination when enough candidates found:
```python
# Stop early if we have enough good candidates
if len(candidate_albums) >= 15:
    break
```

## Results

### Before Fix
- **Matched**: 72/80 performances (90%)
- **Missing**: 8 performances
- **Issues**: 
  - Tracks matched to wrong years (2019, 2023)
  - Excessive API calls causing rate limiting
  - Script crashes on Apple Music 403 errors

### After Fix
- **Matched**: 80/80 performances (100%) ✅
- **Missing**: 0 performances
- **Improvements**:
  - All tracks from correct 2025 albums
  - Reduced API calls (early termination at 15 candidates)
  - Graceful degradation on rate limits
  - Execution time: ~29-30 seconds

### Verification
```bash
# Run the fixed script
python -m src.nmjanitsjar_scraper.streaming_search \
    --positions apps/band-positions/public/data/brass_positions.json \
    --output-dir apps/band-positions/public/data/streaming \
    --aggregate apps/band-positions/public/data/piece_streaming_links.json \
    --years 2025 \
    --min-year 2012 \
    --band-type brass \
    --credentials config/streaming_credentials.json \
    --overrides config/streaming_overrides.json \
    --cache config/streaming_cache.json
```

**Output**:
```
Skrev 80 streaming-oppføringer for brass til apps/band-positions/public/data/streaming
```

**Breakdown**:
- Total entries: 80
- With Spotify: 80
- With Apple Music: 80  
- With both: 80

## Technical Details

### Key Data Structures

**StreamingLinkFinder** class maintains:
- `_spotify_album_cache`: Cached tracks per (year, division)
- `_apple_album_cache`: Cached tracks per (year, division)
- `_discovered_album_names`: Album name cache (currently disabled for accuracy)

### Album Search Flow

1. **Collect candidates**: Search all terms, gather albums, dedupe by ID
2. **Score albums**: Apply relevance scoring to each album
3. **Sort by score**: Highest scores first (best matches)
4. **Filter by year**: ONLY keep albums from target year
5. **Collect tracks**: Fetch tracks from filtered albums, dedupe by track ID
6. **Match performances**: Use fuzzy string matching (threshold: 0.65)

### Missing Performances Previously

The 8 missing performances were:
1. Follesø Musikklag - "Sinfonietta no. 3" (1. divisjon)
2. Lindås Brass - "Purcell Variations" (2. divisjon)
3. Sørum Musikklag - "St. James's - A New Beginning" (2. divisjon)
4. Trondheim Politis Brassband - "Sinfonietta No. 5" (2. divisjon)
5. Brumunddal Brass - "Lake of the Moon" (5. divisjon)
6. Frei Hornmusikk - "Music for a Festival" (5. divisjon)
7. Haus Musikklag - "Lake of the Moon" (5. divisjon)
8. Eikanger-Bjørsvik Musikklag - Concerto piece (Elite)
9. Tertnes Brass - "Perihelion: Closer to the Sun" (Elite)

**Why they were missing**: Script was matching them to 2019 albums first, then the year filter rejected them.

**Solution**: Filter albums by year BEFORE collecting tracks, ensuring only 2025 albums are considered.

## Testing

### Test for 2025
```bash
python -m src.nmjanitsjar_scraper.streaming_search \
    --years 2025 --band-type brass [...other args]
```
✅ Result: 80/80 matched

### Regression Test for 2024
```bash
python -m src.nmjanitsjar_scraper.streaming_search \
    --years 2024 --band-type brass [...other args]
```
✅ Result: 76/76 matched (with graceful Apple Music rate limit handling)

## Future Improvements

1. **Album Name Caching**: Could be re-enabled with better fuzzy matching logic to reduce API calls further
2. **Parallel API Calls**: Could speed up execution by fetching tracks from multiple albums concurrently
3. **Better Rate Limit Handling**: Could implement exponential backoff for Apple Music
4. **Logging**: Could add structured logging for debugging and monitoring

## Files Modified

- `src/nmjanitsjar_scraper/streaming_search.py` (primary changes)

## Dependencies

- `requests`: HTTP client for API calls
- `tenacity`: Retry logic with exponential backoff
- `rich`: Progress bars and console output

## Conclusion

The streaming search script now correctly matches 100% of available performances to their streaming links for 2025, with improved performance and robust error handling. The fix is production-ready and maintains backward compatibility with previous years.
