# Elite Test Pieces Implementation

## Summary

This document describes the implementation of two improvements for Elite test pieces in the brass band positions application:

1. **Test pieces now appear in the pieces list** - Each Elite band's performance of a test piece shows as a separate row
2. **Streaming links infrastructure ready** - The scraper now processes test pieces and will find streaming links automatically

## Changes Made

### 1. Frontend Changes (`apps/band-positions/src/App.svelte`)

#### Added `addEliteTestPiecePerformances()` Function (Lines 381-442)
- Processes Elite division brass band entries
- Creates piece performance records for test pieces from `elite_test_pieces.json`
- Keeps test piece logic separate from own-choice piece logic
- Each Elite band gets its own performance row with their actual score

**How it works:**
1. Groups all band entries by year
2. For each year with a test piece, finds all Elite division entries
3. Creates or updates a piece record for the test piece
4. Adds a performance entry for each Elite band with their score
5. Uses existing `findStreamingLinkForPiece()` to resolve streaming links

#### Modified `buildPieceRecords()` Function
- Added two new parameters: `eliteTestPiecesData` and `currentBandType`
- For brass bands, calls `addEliteTestPiecePerformances()` after processing own-choice pieces
- Updated all calls to pass the new parameters (lines 850, 1052)

### 2. Backend Changes (`src/nmjanitsjar_scraper/streaming_search.py`)

#### Modified `load_performances()` Function (Line 489)
- Added `elite_test_pieces_path` parameter
- Added `band_type` parameter
- For brass bands with Elite division, automatically loads and includes test pieces
- Test pieces are added as additional Performance objects with correct year/division/band/piece

**How it works:**
1. Loads `elite_test_pieces.json` if processing brass bands
2. After adding own-choice pieces, checks if entry is Elite division
3. Adds the test piece for that year as an additional performance
4. The rest of the scraper treats it like any other piece to find streaming links

#### Modified `generate_streaming_links()` Function (Line 1165)
- Auto-detects `elite_test_pieces.json` path for brass bands
- Passes it to `load_performances()`

## Usage

### Frontend (Already Working)

The frontend changes are complete and working. When you:
1. Switch to "Brass" band type
2. Go to "Pieces" (Stykke) view
3. Click on a test piece (e.g., "Symphony of Colours", "Goldberg 2012")

You will see all 10 Elite bands listed with their individual scores for that year.

### Generating Streaming Links

To fetch streaming links for test pieces, run the existing command as before:

```bash
python -m src.nmjanitsjar_scraper.streaming_search \
    --positions apps/band-positions/public/data/brass_positions.json \
    --output-dir apps/band-positions/public/data/streaming \
    --aggregate apps/band-positions/public/data/piece_streaming_links.json \
    --years 2024 \
    --min-year 2012 \
    --band-type brass \
    --credentials config/streaming_credentials.json \
    --overrides config/streaming_overrides.json \
    --cache config/streaming_cache.json
```

**What's new:**
- The scraper will now automatically include test pieces for Elite bands
- It looks for `elite_test_pieces.json` in the same directory as `brass_positions.json`
- Test pieces are matched against Spotify/Apple Music like any other piece

### Expected Output

After running the scraper for a year (e.g., 2024), `piece_streaming_links.json` should contain entries like:

```json
{
  "year": 2024,
  "division": "Elite",
  "band": "Eikanger-Bjørsvik Musikklag",
  "result_piece": "Symphony of Colours",
  "recording_title": "Symphony of Colours",
  "album": "NM Brass 2024 - Elitedivisjon",
  "spotify": "https://open.spotify.com/track/...",
  "apple_music": null
}
```

One entry for each of the 10 Elite bands that performed the test piece.

## Files Modified

1. **`apps/band-positions/src/App.svelte`**
   - Added `addEliteTestPiecePerformances()` helper
   - Modified `buildPieceRecords()` signature and implementation
   - Updated function calls

2. **`src/nmjanitsjar_scraper/streaming_search.py`**
   - Modified `load_performances()` to include test pieces
   - Modified `generate_streaming_links()` to pass test pieces path

## Data Files

### Input Files (Already Exist)
- `apps/band-positions/public/data/brass_positions.json` - Band performance data
- `apps/band-positions/public/data/elite_test_pieces.json` - Test piece definitions per year

### Output Files (Updated by Scraper)
- `apps/band-positions/public/data/piece_streaming_links.json` - Aggregated streaming links
- `apps/band-positions/public/data/streaming/brass_YYYY.json` - Per-year streaming data

## Testing

### Frontend Testing ✅
- Build completed successfully
- Test pieces appear in pieces list
- Each Elite band shows as separate row
- Confirmed working at `localhost:5173`

### Backend Testing (Next Steps)
Run the scraper for a recent year to verify:
1. Test pieces are detected and processed
2. Streaming links are found and saved
3. Links appear in the UI when viewing test pieces

## Architecture Notes

### Design Decisions

1. **Separation of Concerns**
   - Test piece logic is kept separate from own-choice logic
   - Frontend: dedicated helper function
   - Backend: added after regular piece processing

2. **No Data Duplication**
   - Test pieces are NOT added to `brass_positions.json`
   - They remain in `elite_test_pieces.json`
   - Both frontend and backend read from this source

3. **Automatic Detection**
   - Backend automatically finds `elite_test_pieces.json`
   - No new command-line parameters needed
   - Works with existing workflows

### Streaming Link Matching

The matching logic now uses both piece name AND band/artist information:
- Year + Division: Determines which album(s) to search
- Piece name: Primary matching criterion (via title similarity)
- **Band/Artist name: Secondary matching to distinguish performances** (NEW!)

The combined scoring algorithm:
- If artist matches strongly (>70% similarity): 60% piece + 40% artist
- If artist matches moderately (>40% similarity): 80% piece + 20% artist  
- If artist match is weak: 100% piece score only

This ensures:
1. **Test pieces** with the same name are correctly matched to each band's recording
2. **Own-choice pieces** that multiple bands perform are correctly distinguished
3. Albums contain tracks with artist metadata (band name) for accurate matching

## Future Enhancements

Potential improvements for the future:

1. **Test Piece Indicators in UI**
   - Already implemented! Test pieces show with "P:" label in band performances view
   - Consider adding similar indicators in pieces list

2. **Composer Linking**
   - Test pieces already include composer info from `elite_test_pieces.json`
   - Composers are linkable in the pieces view

3. **Historical Data**
   - Run scraper for all years since 2012 to populate streaming links for historical test pieces
   - Consider batch processing multiple years

4. **Error Handling**
   - Scraper gracefully handles missing `elite_test_pieces.json`
   - Consider logging which test pieces were processed

## Questions?

If you encounter any issues:
1. Check that `elite_test_pieces.json` exists in the correct location
2. Verify the JSON structure matches expected format
3. Run scraper with `--years` for a specific year to test
4. Check browser console for any errors when viewing pieces
