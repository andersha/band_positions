#!/usr/bin/env python3
"""
Quick analysis script for Norwegian Wind Band Orchestra data.
Run this for a fast overview of your dataset!
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    # Load data
    print("🎺 Loading Norwegian Wind Band Orchestra Competition Data...")
    df = pd.read_csv('data/processed/all_placements.csv')
    
    print(f"📊 Dataset Overview:")
    print(f"   • Total placements: {len(df):,}")
    print(f"   • Years covered: {df['year'].min()}-{df['year'].max()}")
    print(f"   • Unique orchestras: {df['orchestra'].nunique():,}")
    print(f"   • Unique conductors: {df['conductor'].nunique():,}")
    print(f"   • Divisions: {df['division'].nunique()}")
    
    # Quick visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Participation over time
    yearly_counts = df.groupby('year').size()
    ax1.plot(yearly_counts.index, yearly_counts.values, marker='o', linewidth=2)
    ax1.set_title('🎺 Orchestra Participation Over Time')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Orchestras')
    ax1.grid(True, alpha=0.3)
    
    # 2. Top winning orchestras
    winners = df[df['rank'] == 1]['orchestra'].value_counts().head(10)
    ax2.barh(range(len(winners)), winners.values, color='gold')
    ax2.set_yticks(range(len(winners)))
    ax2.set_yticklabels([name.split()[-1][:15] for name in winners.index])
    ax2.set_title('🏆 Top 10 Winning Orchestras')
    ax2.set_xlabel('Number of Wins')
    
    # 3. Points distribution by division
    divisions = df['division'].unique()
    division_points = []
    division_names = []
    
    for div in sorted(divisions):
        points = df[df['division'] == div]['points'].dropna()
        if len(points) > 0:
            division_points.append(points)
            division_names.append(div)
    
    if division_points:
        ax3.boxplot(division_points, labels=division_names)
        ax3.set_title('📊 Score Distribution by Division')
        ax3.set_ylabel('Points')
        ax3.tick_params(axis='x', rotation=45)
    
    # 4. Competition growth by decade
    df['decade'] = (df['year'] // 10) * 10
    decade_counts = df.groupby('decade').size()
    ax4.bar(decade_counts.index, decade_counts.values, color='steelblue', alpha=0.7)
    ax4.set_title('🚀 Competition Activity by Decade')
    ax4.set_xlabel('Decade')
    ax4.set_ylabel('Total Placements')
    
    plt.tight_layout()
    plt.savefig('competition_overview.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Show top performers
    print(f"\n🏆 All-Time Champions (Top 10):")
    winners_detailed = df[df['rank'] == 1]['orchestra'].value_counts().head(10)
    for i, (orchestra, wins) in enumerate(winners_detailed.items(), 1):
        print(f"   {i:2}. {orchestra}: {wins} wins")
    
    # Show recent champions (if available)
    recent_data = df[df['year'] >= 2020]
    if len(recent_data) > 0:
        print(f"\n🔥 Recent Champions (2020+):")
        recent_winners = recent_data[recent_data['rank'] == 1]
        for _, row in recent_winners.iterrows():
            print(f"   {row['year']}: {row['orchestra']} ({row['division']})")
    
    print(f"\n📈 Key Statistics:")
    print(f"   • Average score: {df['points'].mean():.1f} points")
    print(f"   • Highest score ever: {df['points'].max():.1f} points")
    print(f"   • Most active decade: {decade_counts.idxmax()}s ({decade_counts.max()} competitions)")
    print(f"   • Peak year: {yearly_counts.idxmax()} ({yearly_counts.max()} orchestras)")
    
    print(f"\n💾 Visualization saved as 'competition_overview.png'")
    print(f"📓 For detailed analysis, open: notebooks/competition_analysis.ipynb")

if __name__ == "__main__":
    main()
