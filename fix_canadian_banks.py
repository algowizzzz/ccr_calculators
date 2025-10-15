#!/usr/bin/env python3
"""
Fix processing for Canadian banks by creating proper key metrics files.
The issue is that ticker names with slashes create invalid filenames.
"""

import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.append('src')
from extract_key_metrics import extract_key_metrics
from analyze_metrics import analyze_all_metrics

# Mapping of CIK to proper ticker names (without slashes)
canadian_banks = {
    '0001000275': {'ticker': 'RY', 'name': 'Royal Bank of Canada'},
    '0000947263': {'ticker': 'TD', 'name': 'Toronto-Dominion Bank'},
    '0000009631': {'ticker': 'BNS', 'name': 'Bank of Nova Scotia'},
    '0000927971': {'ticker': 'BMO', 'name': 'Bank of Montreal'},
    '0001045520': {'ticker': 'CM', 'name': 'Canadian Imperial Bank of Commerce'}
}

def process_canadian_bank(cik, bank_info):
    """Process a single Canadian bank"""
    raw_file = Path(f"sec_metrics_data/raw_json/companyfacts_{cik}.json")
    
    if not raw_file.exists():
        print(f"❌ Raw file not found: {raw_file}")
        return False
    
    try:
        # Load raw data
        with open(raw_file, 'r') as f:
            raw_data = json.load(f)
        
        print(f"✓ Processing {bank_info['name']} ({bank_info['ticker']})")
        
        # Extract key metrics
        key_metrics = extract_key_metrics(raw_data)
        
        # Save key metrics with proper filename
        metrics_file = Path(f"sec_metrics_data/key_metrics/{bank_info['ticker'].lower()}_key_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(key_metrics, f, indent=2, default=str)
        print(f"  ✓ Saved: {metrics_file}")
        
        # Generate catalog
        catalog = analyze_all_metrics(raw_data)
        catalog_file = Path(f"sec_metrics_data/catalogs/{bank_info['ticker'].lower()}_catalog.json")
        with open(catalog_file, 'w') as f:
            json.dump(catalog, f, indent=2, default=str)
        print(f"  ✓ Saved: {catalog_file}")
        
        # Create summary
        summary = {
            'company_name': raw_data.get('entityName'),
            'ticker': bank_info['ticker'],
            'cik': cik,
            'processing_date': '2025-09-30T10:00:00',
            'total_metrics': catalog['summary']['total_metrics'],
            'taxonomies': list(catalog['taxonomies'].keys()),
            'key_metrics_found': sum(1 for m in key_metrics['metrics'].values() if m['sec_key'] is not None),
            'key_metrics_total': len(key_metrics['metrics']),
            'categories': dict(catalog['summary']['categories']),
            'date_range': {'earliest': None, 'latest': None}
        }
        
        # Find date range
        all_dates = []
        for taxonomy_data in catalog['taxonomies'].values():
            for metric_info in taxonomy_data['metrics'].values():
                if metric_info['date_range']['earliest']:
                    all_dates.append(metric_info['date_range']['earliest'])
                if metric_info['date_range']['latest']:
                    all_dates.append(metric_info['date_range']['latest'])
        
        if all_dates:
            summary['date_range']['earliest'] = min(all_dates)
            summary['date_range']['latest'] = max(all_dates)
        
        summary_file = Path(f"sec_metrics_data/summaries/{bank_info['ticker'].lower()}_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"  ✓ Saved: {summary_file}")
        
        print(f"  📊 Total metrics: {summary['total_metrics']}")
        print(f"  📊 Key metrics found: {summary['key_metrics_found']}/29")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {bank_info['name']}: {e}")
        return False

def main():
    print("🇨🇦 Processing Canadian Banks")
    print("=" * 50)
    
    successful = 0
    for cik, bank_info in canadian_banks.items():
        if process_canadian_bank(cik, bank_info):
            successful += 1
        print()
    
    print(f"✅ Successfully processed {successful}/{len(canadian_banks)} Canadian banks")

if __name__ == "__main__":
    main()
