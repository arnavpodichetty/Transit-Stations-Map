#!/usr/bin/env python3
"""
Data setup script for Transit Map application.
This script runs the data processing pipeline to prepare JSON files from GeoJSON sources.
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Script {script_name} not found")
        return False
    return True

def copy_data_files():
    """Copy processed JSON files to the app's public directory."""
    data_dir = Path("data")
    app_data_dir = Path("app/public/data")
    
    # Create app data directory if it doesn't exist
    app_data_dir.mkdir(parents=True, exist_ok=True)
    
    # List of files to copy
    files_to_copy = [
        "data.json",
        "routes.json", 
        "bottlenecks.json",
        "low_income.json"
    ]
    
    print("📁 Copying data files to app directory...")
    
    for filename in files_to_copy:
        src = data_dir / filename
        dst = app_data_dir / filename
        
        if src.exists():
            import shutil
            shutil.copy2(src, dst)
            print(f"✅ Copied {filename}")
        else:
            print(f"⚠️  {filename} not found, skipping")

def main():
    """Main function to run the data setup pipeline."""
    print("🗺️  Transit Map Data Setup")
    print("=" * 40)
    
    # Check if required source files exist
    required_files = [
        "ca_filter.py",
        "convert_geojson_to_json.py"
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    # Run the data processing pipeline
    success = True
    
    success &= run_script("ca_filter.py", "Filtering California data")
    success &= run_script("convert_geojson_to_json.py", "Converting GeoJSON to JSON")
    
    if success:
        copy_data_files()
        print("\n🎉 Data setup completed successfully!")
        print("You can now run: python run_dev.py")
    else:
        print("\n❌ Data setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()