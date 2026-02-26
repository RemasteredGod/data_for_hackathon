#!/usr/bin/env python3
"""Main entry point for PRGI Data Search Application.

This script automatically launches the Streamlit web application.
Run: python main.py
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import streamlit
        import pandas
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✅ Dependencies installed successfully!")

def check_database():
    """Check if database exists, if not guide user to create it."""
    db_path = Path("prgi_data.db")
    csv_path = Path("prgi_registration_title_details.csv")
    
    if not db_path.exists():
        print("\n⚠️  Database not found!")
        if csv_path.exists():
            print("📊 CSV file found. Importing data into database...")
            print("This may take a minute...\n")
            subprocess.check_call([
                sys.executable, 
                "prgi_data_manager.py", 
                "import", 
                "--csv", str(csv_path),
                "--db", str(db_path)
            ])
            print("\n✅ Database created successfully!")
        else:
            print(f"❌ CSV file '{csv_path}' not found!")
            print("\nPlease either:")
            print(f"  1. Place your CSV file as '{csv_path}'")
            print(f"  2. Run the scraper: python scrape_prgi.py")
            print(f"  3. Manually import: python prgi_data_manager.py import --csv <your_file.csv>\n")
            return False
    else:
        print("✅ Database found!")
    
    return True

def launch_app():
    """Launch the Streamlit application."""
    print("\n🚀 Starting PRGI Data Search Application...")
    print("📱 The app will open in your default browser")
    print("🔗 URL: http://localhost:8501")
    print("\n💡 Press Ctrl+C to stop the server\n")
    print("="*60)
    
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.port=8501",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped. Goodbye!")
        sys.exit(0)

def main():
    """Main execution function."""
    print("="*60)
    print("🔍 PRGI Data Search - Database Management System")
    print("="*60)
    
    print("\n📋 Checking system requirements...")
    check_dependencies()
    
    if not check_database():
        sys.exit(1)
    
    launch_app()

if __name__ == "__main__":
    main()
