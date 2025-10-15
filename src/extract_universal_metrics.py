#!/usr/bin/env python3
"""
Extract universal metrics - metrics found across most banks.
This gives us a comprehensive dataset based on actual availability rather than pre-selected metrics.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_metric_universality(raw_json_dir):
    """Analyze which metrics are found across multiple banks"""
    
    json_files = list(Path(raw_json_dir).glob("*.json"))
    
    # Track metrics across all banks
    metric_bank_count = defaultdict(set)  # metric_name -> set of banks
    metric_metadata = defaultdict(lambda: {
        'labels': set(),
        'descriptions': set(),
        'units': set(),
        'taxonomies': set()
    })
    
    bank_names = {}  # CIK -> bank name
    
    print(f"🔍 Analyzing {len(json_files)} banks for universal metrics...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            company_name = data.get('entityName', 'Unknown')
            cik = str(data.get('cik', 'Unknown'))
            bank_names[cik] = company_name
            
            facts = data.get('facts', {})
            
            # Track each metric
            for taxonomy_name, taxonomy_data in facts.items():
                for metric_name, metric_data in taxonomy_data.items():
                    metric_bank_count[metric_name].add(company_name)
                    metric_metadata[metric_name]['taxonomies'].add(taxonomy_name)
                    
                    if 'label' in metric_data:
                        metric_metadata[metric_name]['labels'].add(metric_data['label'])
                    if 'description' in metric_data:
                        metric_metadata[metric_name]['descriptions'].add(metric_data['description'])
                    
                    # Track units
                    units = metric_data.get('units', {})
                    for unit_name in units.keys():
                        metric_metadata[metric_name]['units'].add(unit_name)
        
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    return metric_bank_count, metric_metadata, bank_names

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
    
    # Last resort: any data
    if unit_data:
        latest = max(unit_data, key=lambda x: x.get('end', ''))
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

def extract_universal_metrics(raw_json_dir, min_bank_threshold=15):
    """Extract universal metrics found in at least min_bank_threshold banks"""
    
    # Analyze universality
    metric_bank_count, metric_metadata, bank_names = analyze_metric_universality(raw_json_dir)
    
    # Filter for universal metrics
    universal_metrics = {}
    for metric_name, banks in metric_bank_count.items():
        if len(banks) >= min_bank_threshold:
            metadata = metric_metadata[metric_name]
            universal_metrics[metric_name] = {
                'bank_count': len(banks),
                'banks': sorted(list(banks)),
                'labels': list(metadata['labels']),
                'descriptions': list(metadata['descriptions']),
                'units': list(metadata['units']),
                'taxonomies': list(metadata['taxonomies']),
                'primary_label': list(metadata['labels'])[0] if metadata['labels'] else None,
                'primary_description': list(metadata['descriptions'])[0] if metadata['descriptions'] else None
            }
    
    print(f"📊 Found {len(universal_metrics)} universal metrics (≥{min_bank_threshold} banks)")
    
    # Now extract actual values for each bank
    json_files = list(Path(raw_json_dir).glob("*.json"))
    bank_data = {}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            company_name = data.get('entityName', 'Unknown')
            cik = str(data.get('cik', 'Unknown'))
            
            bank_metrics = {
                'company_info': {
                    'name': company_name,
                    'cik': cik,
                    'extraction_date': datetime.now().isoformat()
                },
                'metrics': {}
            }
            
            facts = data.get('facts', {})
            
            # Extract each universal metric for this bank
            for metric_name in universal_metrics.keys():
                # Find the metric in any taxonomy
                metric_data = None
                found_taxonomy = None
                
                for taxonomy_name, taxonomy_data in facts.items():
                    if metric_name in taxonomy_data:
                        metric_data = taxonomy_data[metric_name]
                        found_taxonomy = taxonomy_name
                        break
                
                if metric_data:
                    # Get the latest value
                    latest_value = get_latest_value(metric_data)
                    
                    bank_metrics['metrics'][metric_name] = {
                        'taxonomy': found_taxonomy,
                        'label': metric_data.get('label'),
                        'description': metric_data.get('description'),
                        'latest_value': latest_value,
                        'available_units': list(metric_data.get('units', {}).keys()),
                        'data_points_count': sum(len(points) for points in metric_data.get('units', {}).values())
                    }
                else:
                    # Metric not found for this bank (shouldn't happen for universal metrics)
                    bank_metrics['metrics'][metric_name] = {
                        'taxonomy': None,
                        'label': None,
                        'description': None,
                        'latest_value': None,
                        'available_units': [],
                        'data_points_count': 0
                    }
            
            bank_data[company_name] = bank_metrics
            
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    return universal_metrics, bank_data

def generate_summary_report(universal_metrics, bank_data, min_threshold):
    """Generate a summary report of universal metrics"""
    
    print("\n" + "=" * 100)
    print("🌟 UNIVERSAL SEC METRICS EXTRACTION REPORT")
    print("=" * 100)
    
    print(f"📊 OVERVIEW:")
    print(f"  • Universal Metrics Found: {len(universal_metrics)} (≥{min_threshold} banks)")
    print(f"  • Banks Analyzed: {len(bank_data)}")
    
    # Sort metrics by bank count
    sorted_metrics = sorted(universal_metrics.items(), key=lambda x: x[1]['bank_count'], reverse=True)
    
    print(f"\n🔝 TOP UNIVERSAL METRICS:")
    print(f"{'Metric Name':60} | {'Banks':5} | {'Units':15} | {'Label'}")
    print("-" * 120)
    
    for i, (metric_name, data) in enumerate(sorted_metrics[:20], 1):
        units_str = ", ".join(data['units'][:3])  # Show first 3 units
        if len(data['units']) > 3:
            units_str += "..."
        label = data['primary_label'] or "No label"
        print(f"{metric_name[:59]:59} | {data['bank_count']:5d} | {units_str[:14]:14} | {label[:40]}")
    
    # Categorize metrics
    categories = {
        'Assets': ['asset', 'cash', 'receivable', 'inventory', 'securities', 'property'],
        'Liabilities': ['liabilit', 'payable', 'debt', 'accrued'],
        'Equity': ['equity', 'stock', 'share', 'capital', 'retained'],
        'Income': ['income', 'revenue', 'earnings', 'profit', 'loss'],
        'Expenses': ['expense', 'cost', 'interest'],
        'Tax': ['tax', 'deferred'],
        'Banking': ['loan', 'deposit', 'allowance', 'credit'],
        'Derivatives': ['derivative', 'fair value', 'hedge'],
        'Cash Flow': ['cash flow', 'cashflow'],
        'Other': []
    }
    
    categorized = defaultdict(list)
    for metric_name, data in universal_metrics.items():
        metric_lower = metric_name.lower()
        label_lower = (data['primary_label'] or '').lower()
        
        categorized_flag = False
        for category, keywords in categories.items():
            if category == 'Other':
                continue
            if any(keyword in metric_lower or keyword in label_lower for keyword in keywords):
                categorized[category].append((metric_name, data['bank_count']))
                categorized_flag = True
                break
        
        if not categorized_flag:
            categorized['Other'].append((metric_name, data['bank_count']))
    
    print(f"\n📋 UNIVERSAL METRICS BY CATEGORY:")
    for category, metrics in categorized.items():
        if metrics:
            metrics.sort(key=lambda x: x[1], reverse=True)
            print(f"\n  {category} ({len(metrics)} metrics):")
            for metric_name, bank_count in metrics[:8]:  # Top 8 per category
                print(f"    • {metric_name:50} ({bank_count} banks)")
    
    # Data completeness analysis
    print(f"\n📈 DATA COMPLETENESS ANALYSIS:")
    completeness_stats = []
    for bank_name, bank_data_item in bank_data.items():
        metrics_with_data = sum(1 for m in bank_data_item['metrics'].values() if m['latest_value'] is not None)
        total_metrics = len(bank_data_item['metrics'])
        completeness = (metrics_with_data / total_metrics * 100) if total_metrics > 0 else 0
        completeness_stats.append((bank_name, completeness, metrics_with_data, total_metrics))
    
    completeness_stats.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'Bank Name':45} | {'Completeness':11} | {'With Data':9} | {'Total'}")
    print("-" * 80)
    for bank_name, completeness, with_data, total in completeness_stats[:15]:
        print(f"{bank_name[:44]:44} | {completeness:10.1f}% | {with_data:9d} | {total}")

def main():
    parser = argparse.ArgumentParser(description='Extract universal SEC metrics found across most banks')
    parser.add_argument('--raw-json-dir', default='sec_metrics_data/raw_json',
                       help='Directory containing raw SEC JSON files')
    parser.add_argument('--output-dir', default='sec_metrics_data',
                       help='Output directory for universal metrics')
    parser.add_argument('--min-banks', type=int, default=15,
                       help='Minimum number of banks a metric must appear in to be considered universal')
    parser.add_argument('--output-format', choices=['json', 'both'], default='both',
                       help='Output format')
    
    args = parser.parse_args()
    
    print(f"🔍 Extracting universal metrics (≥{args.min_banks} banks)...")
    print(f"📁 Raw JSON directory: {args.raw_json_dir}")
    print("=" * 80)
    
    # Extract universal metrics
    universal_metrics, bank_data = extract_universal_metrics(args.raw_json_dir, args.min_banks)
    
    # Generate report
    generate_summary_report(universal_metrics, bank_data, args.min_banks)
    
    # Save results
    output_data = {
        'extraction_metadata': {
            'extraction_date': datetime.now().isoformat(),
            'min_bank_threshold': args.min_banks,
            'total_banks_analyzed': len(bank_data),
            'total_universal_metrics': len(universal_metrics)
        },
        'universal_metrics_catalog': universal_metrics,
        'bank_data': bank_data
    }
    
    # Save comprehensive data
    if args.output_format in ['json', 'both']:
        output_file = Path(args.output_dir) / f"universal_metrics_min{args.min_banks}.json"
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n💾 Universal metrics saved: {output_file}")
    
    # Save individual bank files for easy access
    bank_dir = Path(args.output_dir) / "universal_metrics"
    bank_dir.mkdir(exist_ok=True)
    
    for bank_name, data in bank_data.items():
        # Clean filename
        safe_name = "".join(c for c in bank_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
        
        bank_file = bank_dir / f"{safe_name}_universal_metrics.json"
        with open(bank_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    print(f"💾 Individual bank files saved: {bank_dir}")
    print(f"\n✅ Extraction complete! Found {len(universal_metrics)} universal metrics across {len(bank_data)} banks")

if __name__ == "__main__":
    main()

