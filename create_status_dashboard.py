#!/usr/bin/env python3
"""
Create a status dashboard for the SEC metrics data collection.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def create_dashboard():
    base_dir = Path("sec_metrics_data")
    
    # Count files in each directory
    raw_json_count = len(list((base_dir / "raw_json").glob("*.json"))) if (base_dir / "raw_json").exists() else 0
    key_metrics_count = len(list((base_dir / "key_metrics").glob("*.json"))) if (base_dir / "key_metrics").exists() else 0
    catalogs_count = len(list((base_dir / "catalogs").glob("*.json"))) if (base_dir / "catalogs").exists() else 0
    summaries_count = len(list((base_dir / "summaries").glob("*.json"))) if (base_dir / "summaries").exists() else 0
    
    # Get list of processed companies
    processed_companies = []
    if (base_dir / "key_metrics").exists():
        for file in (base_dir / "key_metrics").glob("*.json"):
            ticker = file.stem.replace("_key_metrics", "").upper()
            processed_companies.append(ticker)
    
    processed_companies.sort()
    
    # Calculate total file sizes
    total_size = 0
    if base_dir.exists():
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
    
    # Create dashboard
    dashboard = {
        "sec_metrics_data_status": {
            "last_updated": datetime.now().isoformat(),
            "summary": {
                "companies_processed": key_metrics_count,
                "total_target": 30,
                "completion_percentage": f"{(key_metrics_count/30*100):.1f}%",
                "total_data_size_mb": f"{total_size/(1024*1024):.1f} MB"
            },
            "files_created": {
                "raw_json": raw_json_count,
                "key_metrics": key_metrics_count,
                "catalogs": catalogs_count,
                "summaries": summaries_count,
                "total_files": raw_json_count + key_metrics_count + catalogs_count + summaries_count
            },
            "processed_companies": processed_companies,
            "remaining_companies": [
                "ALLY", "BMO", "BNS", "CFG", "CM", "CMA", "FCNCA", "KEY", "MTB", "NA", "RY", "TD", "ZION"
            ] if key_metrics_count < 30 else []
        }
    }
    
    return dashboard

if __name__ == "__main__":
    dashboard = create_dashboard()
    
    print("=" * 80)
    print("SEC METRICS DATA COLLECTION STATUS")
    print("=" * 80)
    print(f"Last Updated: {dashboard['sec_metrics_data_status']['last_updated']}")
    print()
    
    summary = dashboard['sec_metrics_data_status']['summary']
    print("PROGRESS SUMMARY:")
    print(f"  Companies Processed: {summary['companies_processed']}/{summary['total_target']} ({summary['completion_percentage']})")
    print(f"  Total Data Size: {summary['total_data_size_mb']}")
    print()
    
    files = dashboard['sec_metrics_data_status']['files_created']
    print("FILES CREATED:")
    print(f"  Raw JSON files: {files['raw_json']}")
    print(f"  Key Metrics files: {files['key_metrics']}")  
    print(f"  Catalog files: {files['catalogs']}")
    print(f"  Summary files: {files['summaries']}")
    print(f"  Total files: {files['total_files']}")
    print()
    
    processed = dashboard['sec_metrics_data_status']['processed_companies']
    print("PROCESSED COMPANIES:")
    print(f"  {', '.join(processed)}")
    print()
    
    remaining = dashboard['sec_metrics_data_status']['remaining_companies']
    if remaining:
        print("REMAINING COMPANIES:")
        print(f"  {', '.join(remaining)}")
    else:
        print("✅ ALL COMPANIES PROCESSED!")
    
    # Save dashboard
    with open('sec_metrics_data/status_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n📊 Dashboard saved: sec_metrics_data/status_dashboard.json")

