#!/usr/bin/env python3
"""
Script to run WindRep analysis programmatically
"""

from src.nmjanitsjar_scraper.piece_analysis import PieceAnalyzer

def main():
    # Initialize analyzer
    analyzer = PieceAnalyzer()
    
    print("🎼 Getting most popular pieces...")
    popular_pieces = analyzer.get_most_popular_pieces(min_performances=3)
    
    print(f"✓ Found {len(popular_pieces)} popular pieces")
    print(f"✓ Top piece: '{popular_pieces[0].title}' by {popular_pieces[0].composer} ({popular_pieces[0].performance_count} performances)")
    
    # Enrich with WindRep data (adjust max_pieces as needed)
    print(f"\n🌐 Enriching top 50 pieces with WindRep data...")
    enriched_pieces = analyzer.enrich_with_windrep_data(popular_pieces, max_pieces=50)
    
    # Count how many pieces got enriched
    pieces_with_duration = sum(1 for p in enriched_pieces if p.duration_minutes)
    pieces_with_grade = sum(1 for p in enriched_pieces if p.grade_level)
    pieces_with_url = sum(1 for p in enriched_pieces if p.windrep_url)
    
    print(f"\n📊 Results:")
    print(f"✓ {pieces_with_url} pieces found on WindRep")
    print(f"✓ {pieces_with_duration} pieces with duration data")
    print(f"✓ {pieces_with_grade} pieces with grade level data")
    
    # Show some examples
    print(f"\n🎵 Sample enriched pieces:")
    for i, piece in enumerate(enriched_pieces[:5]):
        duration = f"{piece.duration_minutes:.1f}min" if piece.duration_minutes else "Unknown"
        grade = f"Grade {piece.grade_level}" if piece.grade_level else "Unknown"
        print(f"  {i+1}. {piece.title} - {duration}, {grade}")
    
    # Analyze set test pieces
    print(f"\n🔍 Analyzing potential set test pieces...")
    set_pieces = analyzer.analyze_set_test_pieces()
    print(f"✓ Found {sum(len(pieces) for pieces in set_pieces.values())} potential mandatory pieces")
    
    return enriched_pieces

if __name__ == "__main__":
    enriched_pieces = main()
