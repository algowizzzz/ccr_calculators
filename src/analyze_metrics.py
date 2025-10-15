#!/usr/bin/env python3
"""
Analyze SEC companyfacts JSON to extract all available metrics and create a structured catalog.

Usage:
  python analyze_metrics.py --input companyfacts_0000320193.json --output metrics_catalog.json
  python analyze_metrics.py --input companyfacts_0000320193.json --format markdown
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_metric_structure(metric_data):
    """Analyze the structure of a single metric"""
    info = {
        'label': metric_data.get('label', 'N/A'),
        'description': metric_data.get('description', 'N/A'),
        'units': list(metric_data.get('units', {}).keys()),
        'data_points_count': 0,
        'date_range': {'earliest': None, 'latest': None},
        'forms_available': set(),
        'fiscal_years': set(),
        'fiscal_periods': set()
    }
    
    # Analyze all data points across all units
    for unit, data_points in metric_data.get('units', {}).items():
        info['data_points_count'] += len(data_points)
        
        for point in data_points:
            # Track date range
            end_date = point.get('end')
            if end_date:
                if not info['date_range']['earliest'] or end_date < info['date_range']['earliest']:
                    info['date_range']['earliest'] = end_date
                if not info['date_range']['latest'] or end_date > info['date_range']['latest']:
                    info['date_range']['latest'] = end_date
            
            # Track forms, fiscal years, and periods
            if point.get('form'):
                info['forms_available'].add(point['form'])
            if point.get('fy'):
                info['fiscal_years'].add(point['fy'])
            if point.get('fp'):
                info['fiscal_periods'].add(point['fp'])
    
    # Convert sets to sorted lists for JSON serialization
    info['forms_available'] = sorted(list(info['forms_available']))
    info['fiscal_years'] = sorted(list(info['fiscal_years']))
    info['fiscal_periods'] = sorted(list(info['fiscal_periods']))
    
    return info

def categorize_metrics(metric_name, label, description):
    """Categorize metrics based on name, label, and description"""
    name_lower = metric_name.lower() if metric_name else ""
    label_lower = label.lower() if label else ""
    desc_lower = description.lower() if description else ""
    
    # Income Statement metrics
    if any(keyword in name_lower for keyword in ['revenue', 'income', 'earnings', 'profit', 'loss', 'cost', 'expense']):
        if 'operating' in name_lower or 'operating' in label_lower:
            return 'Income Statement - Operating'
        elif 'net' in name_lower or 'net' in label_lower:
            return 'Income Statement - Net'
        else:
            return 'Income Statement - General'
    
    # Balance Sheet - Assets
    elif any(keyword in name_lower for keyword in ['asset', 'cash', 'receivable', 'inventory', 'securities', 'property', 'plant', 'equipment']):
        if 'current' in name_lower or 'current' in label_lower:
            return 'Balance Sheet - Current Assets'
        elif 'noncurrent' in name_lower or 'non-current' in label_lower:
            return 'Balance Sheet - Non-Current Assets'
        else:
            return 'Balance Sheet - Assets'
    
    # Balance Sheet - Liabilities
    elif any(keyword in name_lower for keyword in ['liabilit', 'payable', 'debt', 'accrued', 'deferred']):
        if 'current' in name_lower or 'current' in label_lower:
            return 'Balance Sheet - Current Liabilities'
        elif 'noncurrent' in name_lower or 'non-current' in label_lower:
            return 'Balance Sheet - Non-Current Liabilities'
        else:
            return 'Balance Sheet - Liabilities'
    
    # Balance Sheet - Equity
    elif any(keyword in name_lower for keyword in ['equity', 'stock', 'share', 'capital', 'retained', 'dividend']):
        return 'Balance Sheet - Equity'
    
    # Cash Flow Statement
    elif any(keyword in name_lower for keyword in ['cashflow', 'cash flow', 'financing', 'investing', 'operating']):
        if 'operating' in name_lower or 'operating' in label_lower:
            return 'Cash Flow - Operating Activities'
        elif 'investing' in name_lower or 'investing' in label_lower:
            return 'Cash Flow - Investing Activities'
        elif 'financing' in name_lower or 'financing' in label_lower:
            return 'Cash Flow - Financing Activities'
        else:
            return 'Cash Flow - General'
    
    # Per Share metrics
    elif 'pershare' in name_lower or 'per share' in label_lower:
        return 'Per Share Metrics'
    
    # Entity Information
    elif any(keyword in name_lower for keyword in ['entity', 'common', 'outstanding', 'weighted']):
        return 'Entity Information'
    
    # Other/Uncategorized
    else:
        return 'Other/Uncategorized'

def analyze_all_metrics(companyfacts_data):
    """Analyze all metrics in the companyfacts JSON"""
    results = {
        'company_info': {
            'cik': companyfacts_data.get('cik'),
            'entityName': companyfacts_data.get('entityName'),
            'analysis_date': datetime.now().isoformat()
        },
        'taxonomies': {},
        'metrics_by_category': defaultdict(dict),
        'summary': {
            'total_taxonomies': 0,
            'total_metrics': 0,
            'categories': defaultdict(int)
        }
    }
    
    facts = companyfacts_data.get('facts', {})
    
    for taxonomy_name, taxonomy_data in facts.items():
        print(f"Analyzing taxonomy: {taxonomy_name}")
        
        taxonomy_info = {
            'metrics_count': len(taxonomy_data),
            'metrics': {}
        }
        
        for metric_name, metric_data in taxonomy_data.items():
            # Analyze individual metric
            metric_info = analyze_metric_structure(metric_data)
            
            # Categorize the metric
            category = categorize_metrics(metric_name, metric_info['label'], metric_info['description'])
            
            # Add to taxonomy info
            taxonomy_info['metrics'][metric_name] = metric_info
            
            # Add to categorized view
            results['metrics_by_category'][category][metric_name] = {
                'taxonomy': taxonomy_name,
                'label': metric_info['label'],
                'description': metric_info['description'],
                'units': metric_info['units'],
                'data_points': metric_info['data_points_count'],
                'date_range': metric_info['date_range'],
                'forms': metric_info['forms_available']
            }
            
            # Update summary
            results['summary']['categories'][category] += 1
        
        results['taxonomies'][taxonomy_name] = taxonomy_info
        results['summary']['total_taxonomies'] += 1
        results['summary']['total_metrics'] += len(taxonomy_data)
    
    # Convert defaultdict to regular dict for JSON serialization
    results['metrics_by_category'] = dict(results['metrics_by_category'])
    results['summary']['categories'] = dict(results['summary']['categories'])
    
    return results

def output_json(results, output_path):
    """Output results as JSON"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

def output_markdown(results, output_path):
    """Output results as Markdown"""
    with open(output_path, 'w') as f:
        f.write(f"# SEC Metrics Catalog\n\n")
        f.write(f"**Company:** {results['company_info']['entityName']}\n")
        f.write(f"**CIK:** {results['company_info']['cik']}\n")
        f.write(f"**Analysis Date:** {results['company_info']['analysis_date']}\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total Taxonomies:** {results['summary']['total_taxonomies']}\n")
        f.write(f"- **Total Metrics:** {results['summary']['total_metrics']}\n\n")
        
        f.write("### Metrics by Category\n\n")
        for category, count in sorted(results['summary']['categories'].items()):
            f.write(f"- **{category}:** {count} metrics\n")
        f.write("\n")
        
        # Detailed metrics by category
        f.write("## Detailed Metrics by Category\n\n")
        
        for category, metrics in sorted(results['metrics_by_category'].items()):
            f.write(f"### {category}\n\n")
            f.write("| Metric Name | Label | Units | Data Points | Date Range |\n")
            f.write("|-------------|-------|-------|-------------|------------|\n")
            
            for metric_name, metric_info in sorted(metrics.items()):
                units_str = ", ".join(metric_info['units']) if metric_info['units'] else "N/A"
                date_range = f"{metric_info['date_range']['earliest']} to {metric_info['date_range']['latest']}" if metric_info['date_range']['earliest'] else "N/A"
                
                f.write(f"| `{metric_name}` | {metric_info['label']} | {units_str} | {metric_info['data_points']} | {date_range} |\n")
            
            f.write("\n")
        
        # Taxonomies overview
        f.write("## Taxonomies Overview\n\n")
        for taxonomy_name, taxonomy_info in sorted(results['taxonomies'].items()):
            f.write(f"### {taxonomy_name}\n\n")
            f.write(f"**Metrics Count:** {taxonomy_info['metrics_count']}\n\n")
            
            f.write("| Metric Name | Label | Description |\n")
            f.write("|-------------|-------|-------------|\n")
            
            for metric_name, metric_info in sorted(taxonomy_info['metrics'].items()):
                # Truncate long descriptions
                description = metric_info['description'] or "N/A"
                desc = description[:100] + "..." if len(description) > 100 else description
                f.write(f"| `{metric_name}` | {metric_info['label']} | {desc} |\n")
            
            f.write("\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze SEC companyfacts JSON and create metrics catalog')
    parser.add_argument('--input', required=True, help='Input companyfacts JSON file')
    parser.add_argument('--output', help='Output file path (default: metrics_catalog.json/.md)')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json', 
                       help='Output format (default: json)')
    
    args = parser.parse_args()
    
    # Load input data
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Analyzing all metrics in SEC companyfacts data...")
    results = analyze_all_metrics(data)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base_name = Path(args.input).stem
        extension = '.md' if args.format == 'markdown' else '.json'
        output_path = f"{base_name}_metrics_catalog{extension}"
    
    # Generate output
    if args.format == 'markdown':
        output_markdown(results, output_path)
    else:
        output_json(results, output_path)
    
    print(f"Generated metrics catalog: {output_path}")
    
    # Print summary
    print(f"\nSUMMARY:")
    print(f"- Total taxonomies: {results['summary']['total_taxonomies']}")
    print(f"- Total metrics: {results['summary']['total_metrics']}")
    print(f"- Categories found: {len(results['summary']['categories'])}")
    
    print(f"\nTop categories by metric count:")
    sorted_categories = sorted(results['summary']['categories'].items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories[:10]:
        print(f"  - {category}: {count} metrics")

if __name__ == "__main__":
    main()
