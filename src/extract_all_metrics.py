#!/usr/bin/env python3
"""
Extract ALL available metrics from each raw JSON file and store as individual company files.
No filtering, no comparison - just complete extraction of every metric for each company.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def get_latest_value(metric_data, unit='USD', prefer_annual=True):
    """Get the most recent value for a metric"""
    units = metric_data.get('units', {})
    
    # Try preferred unit first, then any available unit
    unit_data = units.get(unit)
    if not unit_data:
        available_units = list(units.keys())
        if not available_units:
            return None
        unit_data = units[available_units[0]]
        unit = available_units[0]
    
    if not unit_data:
        return None
    
    # Separate annual and quarterly data
    annual_data = [item for item in unit_data if item.get('form') == '10-K']
    quarterly_data = [item for item in unit_data if item.get('form') == '10-Q']
    other_data = [item for item in unit_data if item.get('form') not in ['10-K', '10-Q']]
    
    # Get latest annual if preferred and available
    if prefer_annual and annual_data:
        latest = max(annual_data, key=lambda x: x.get('end', ''))
        return {
            'value': latest.get('val'),
            'date': latest.get('end'),
            'fiscal_year': latest.get('fy'),
            'form': latest.get('form'),
            'filed': latest.get('filed'),
            'unit': unit,
            'type': 'annual'
        }
    
    # Fall back to quarterly data
    if quarterly_data:
        latest = max(quarterly_data, key=lambda x: x.get('end', ''))
        return {
            'value': latest.get('val'),
            'date': latest.get('end'),
            'fiscal_year': latest.get('fy'),
            'fiscal_period': latest.get('fp'),
            'form': latest.get('form'),
            'filed': latest.get('filed'),
            'unit': unit,
            'type': 'quarterly'
        }
    
    # Last resort: any other data
    if other_data:
        latest = max(other_data, key=lambda x: x.get('end', ''))
        return {
            'value': latest.get('val'),
            'date': latest.get('end'),
            'fiscal_year': latest.get('fy'),
            'fiscal_period': latest.get('fp'),
            'form': latest.get('form'),
            'filed': latest.get('filed'),
            'unit': unit,
            'type': 'other'
        }
    
    return None

def get_all_values(metric_data, limit=None):
    """Get all historical values for a metric (optionally limited)"""
    all_values = []
    units = metric_data.get('units', {})
    
    for unit_name, data_points in units.items():
        for point in data_points:
            all_values.append({
                'value': point.get('val'),
                'date': point.get('end'),
                'fiscal_year': point.get('fy'),
                'fiscal_period': point.get('fp'),
                'form': point.get('form'),
                'filed': point.get('filed'),
                'unit': unit_name,
                'accession': point.get('accn'),
                'frame': point.get('frame')
            })
    
    # Sort by date (most recent first)
    all_values.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    if limit:
        return all_values[:limit]
    return all_values

def extract_all_metrics_for_company(raw_json_file, include_history=False, history_limit=5):
    """Extract ALL metrics for a single company"""
    
    try:
        with open(raw_json_file, 'r') as f:
            data = json.load(f)
        
        company_name = data.get('entityName', 'Unknown')
        cik = str(data.get('cik', 'Unknown'))
        
        print(f"📊 Processing: {company_name}")
        
        # Initialize company data structure
        company_data = {
            'company_info': {
                'name': company_name,
                'cik': cik,
                'extraction_date': datetime.now().isoformat(),
                'extraction_type': 'complete_all_metrics'
            },
            'taxonomies': {},
            'metrics_summary': {
                'total_metrics': 0,
                'total_data_points': 0,
                'taxonomies_count': 0
            },
            'all_metrics': {}
        }
        
        facts = data.get('facts', {})
        
        # Process each taxonomy
        for taxonomy_name, taxonomy_data in facts.items():
            print(f"  📚 Taxonomy: {taxonomy_name} ({len(taxonomy_data)} metrics)")
            
            company_data['taxonomies'][taxonomy_name] = {
                'metrics_count': len(taxonomy_data),
                'metric_names': list(taxonomy_data.keys())
            }
            
            # Process each metric in this taxonomy
            for metric_name, metric_data in taxonomy_data.items():
                # Get basic metadata
                metric_info = {
                    'taxonomy': taxonomy_name,
                    'label': metric_data.get('label'),
                    'description': metric_data.get('description'),
                    'available_units': list(metric_data.get('units', {}).keys()),
                    'data_points_count': sum(len(points) for points in metric_data.get('units', {}).values())
                }
                
                # Get latest value
                metric_info['latest_value'] = get_latest_value(metric_data)
                
                # Optionally include historical data
                if include_history:
                    metric_info['historical_values'] = get_all_values(metric_data, history_limit)
                
                # Calculate date range
                all_dates = []
                for unit_data in metric_data.get('units', {}).values():
                    for point in unit_data:
                        if point.get('end'):
                            all_dates.append(point['end'])
                
                if all_dates:
                    metric_info['date_range'] = {
                        'earliest': min(all_dates),
                        'latest': max(all_dates)
                    }
                else:
                    metric_info['date_range'] = {'earliest': None, 'latest': None}
                
                # Store the complete metric
                company_data['all_metrics'][metric_name] = metric_info
                company_data['metrics_summary']['total_data_points'] += metric_info['data_points_count']
            
            company_data['metrics_summary']['total_metrics'] += len(taxonomy_data)
        
        company_data['metrics_summary']['taxonomies_count'] = len(facts)
        
        return company_data
        
    except Exception as e:
        print(f"❌ Error processing {raw_json_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Extract ALL metrics from each raw SEC JSON file')
    parser.add_argument('--raw-json-dir', default='sec_metrics_data/raw_json',
                       help='Directory containing raw SEC JSON files')
    parser.add_argument('--output-dir', default='sec_metrics_data/complete_metrics',
                       help='Output directory for complete metrics files')
    parser.add_argument('--include-history', action='store_true',
                       help='Include historical data points (makes files much larger)')
    parser.add_argument('--history-limit', type=int, default=5,
                       help='Limit historical data points per metric (default: 5)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all raw JSON files
    raw_json_dir = Path(args.raw_json_dir)
    json_files = list(raw_json_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {raw_json_dir}")
        return
    
    print(f"🔍 Extracting ALL metrics from {len(json_files)} companies...")
    print(f"📁 Raw JSON directory: {raw_json_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Include history: {args.include_history}")
    if args.include_history:
        print(f"📊 History limit: {args.history_limit} data points per metric")
    print("=" * 80)
    
    successful = 0
    failed = 0
    total_metrics = 0
    
    # Process each company
    for json_file in sorted(json_files):
        print(f"\n[{successful + failed + 1}/{len(json_files)}] Processing {json_file.name}...")
        
        # Extract all metrics for this company
        company_data = extract_all_metrics_for_company(
            json_file, 
            args.include_history, 
            args.history_limit
        )
        
        if company_data:
            # Create safe filename
            company_name = company_data['company_info']['name']
            safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
            
            output_file = output_dir / f"{safe_name}_all_metrics.json"
            
            # Save the complete data
            with open(output_file, 'w') as f:
                json.dump(company_data, f, indent=2, default=str)
            
            successful += 1
            total_metrics += company_data['metrics_summary']['total_metrics']
            
            print(f"  ✅ Success: {company_data['metrics_summary']['total_metrics']} metrics")
            print(f"  📁 Saved: {output_file}")
        else:
            failed += 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎉 COMPLETE METRICS EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"📊 Companies processed: {len(json_files)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {(successful/len(json_files)*100):.1f}%")
    print(f"📊 Total metrics extracted: {total_metrics:,}")
    print(f"📊 Average metrics per company: {total_metrics/successful:.0f}" if successful > 0 else "N/A")
    print(f"📁 Output directory: {output_dir}")
    
    if args.include_history:
        print(f"📊 Historical data included (up to {args.history_limit} points per metric)")
    
    print(f"\n💾 All files saved in: {output_dir}")

if __name__ == "__main__":
    main()

