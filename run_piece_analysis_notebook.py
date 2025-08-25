#!/usr/bin/env python3
"""
Launcher script for the Norwegian Wind Band Piece Analysis Jupyter Notebook.

This script starts Jupyter Notebook with the proper environment setup and
launches the comprehensive piece analysis notebook.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the piece analysis Jupyter notebook."""
    
    print("🎵 Norwegian Wind Band Competition - Piece Analysis Notebook Launcher")
    print("=" * 70)
    
    # Check if we're in the right directory
    if not Path("src/nmjanitsjar_scraper").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected structure: src/nmjanitsjar_scraper/")
        return 1
    
    # Check if Jupyter is installed
    try:
        subprocess.run(["jupyter", "--version"], capture_output=True, check=True)
        print("✓ Jupyter Notebook found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Jupyter Notebook not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "jupyter"], check=True)
            print("✓ Jupyter Notebook installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install Jupyter Notebook")
            print("   Please install manually: pip install jupyter")
            return 1
    
    # Check if required packages are installed
    required_packages = ["pandas", "matplotlib", "seaborn", "numpy"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
            print("✓ Required packages installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install required packages")
            return 1
    else:
        print("✓ All required packages found")
    
    # Create notebooks directory if it doesn't exist
    notebooks_dir = Path("notebooks")
    notebooks_dir.mkdir(exist_ok=True)
    
    # Check if notebook exists
    notebook_path = notebooks_dir / "piece_analysis.ipynb"
    if not notebook_path.exists():
        print(f"❌ Notebook not found at {notebook_path}")
        return 1
    
    print(f"✓ Found notebook at {notebook_path}")
    print("\n🚀 Launching Jupyter Notebook...")
    print("\nThe notebook will open in your default web browser.")
    print("Navigate to 'notebooks/piece_analysis.ipynb' if it doesn't open automatically.")
    print("\nNotebook Features:")
    print("• 📊 Interactive data analysis with visualizations")
    print("• 🎵 Piece popularity and success rate analysis")  
    print("• 🎯 Set test piece detection and patterns")
    print("• ⏱️  Duration and time constraint analysis")
    print("• 🎼 Composer performance insights")
    print("• 📈 Comprehensive statistical analysis")
    print("\nPress Ctrl+C in this terminal to stop the notebook server when done.")
    
    try:
        # Start Jupyter Notebook
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path.cwd())  # Add current directory to Python path
        
        subprocess.run([
            "jupyter", "notebook", 
            "--notebook-dir", ".",
            "--ip", "127.0.0.1",
            "--port", "8888",
            "--no-browser" if "--no-browser" in sys.argv else ""
        ], env=env)
        
    except KeyboardInterrupt:
        print("\n\n✓ Jupyter Notebook server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error launching Jupyter: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
