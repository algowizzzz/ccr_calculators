#!/usr/bin/env python3
"""
Build a holistic catalog of ALL metrics available across all banks in raw JSON files.
This gives us the complete universe before we limit to specific metrics.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
import statistics

def analyze_raw_json_structure():
    """Analyze the structure and content of all raw JSON files"""
    
    raw_json_dir = Path("sec_metrics_data/raw_json")
    json_files = list(raw_json_dir.glob("*.json"))
    
    print(f"🔍 Analyzing structure of {len(json_files)} raw SEC JSON files...")
    print("=" * 80)
    
    # Global metrics tracking
    all_metrics = defaultdict(lambda: {
        'count': 0,
        'taxonomies': set(),
        'banks': set(),
        'labels': set(),
        'descriptions': set(),
        'units': set(),
        'sample_values': []
    })
    
    # Taxonomy tracking
    taxonomy_stats = defaultdict(lambda: {
        'banks': set(),
        'metric_count': 0,
        'metrics': set()
    })
    
    # Bank-level stats
    bank_stats = {}
    
    for json_file in sorted(json_files):
        print(f"📊 Processing {json_file.name}...")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            company_name = data.get('entityName', 'Unknown')
            cik = str(data.get('cik', 'Unknown'))
            
            bank_metrics = {
                'company': company_name,
                'cik': cik,
                'taxonomies': {},
                'total_metrics': 0,
                'total_data_points': 0
            }
            
            facts = data.get('facts', {})
            
            # Analyze each taxonomy
            for taxonomy_name, taxonomy_data in facts.items():
                taxonomy_metrics = len(taxonomy_data)
                bank_metrics['taxonomies'][taxonomy_name] = {
                    'metrics': taxonomy_metrics,
                    'metric_names': list(taxonomy_data.keys())
                }
                bank_metrics['total_metrics'] += taxonomy_metrics
                
                # Track taxonomy stats
                taxonomy_stats[taxonomy_name]['banks'].add(company_name)
                taxonomy_stats[taxonomy_name]['metric_count'] += taxonomy_metrics
                taxonomy_stats[taxonomy_name]['metrics'].update(taxonomy_data.keys())
                
                # Analyze each metric in this taxonomy
                for metric_name, metric_data in taxonomy_data.items():
                    # Track global metric occurrence
                    all_metrics[metric_name]['count'] += 1
                    all_metrics[metric_name]['taxonomies'].add(taxonomy_name)
                    all_metrics[metric_name]['banks'].add(company_name)
                    
                    # Collect metadata
                    if 'label' in metric_data:
                        all_metrics[metric_name]['labels'].add(metric_data['label'])
                    if 'description' in metric_data:
                        all_metrics[metric_name]['descriptions'].add(metric_data['description'])
                    
                    # Analyze units and data points
                    units = metric_data.get('units', {})
                    for unit_name, data_points in units.items():
                        all_metrics[metric_name]['units'].add(unit_name)
                        bank_metrics['total_data_points'] += len(data_points)
                        
                        # Sample some values for understanding
                        if len(all_metrics[metric_name]['sample_values']) < 3:
                            for point in data_points[:2]:  # Take first 2 values
                                if 'val' in point:
                                    all_metrics[metric_name]['sample_values'].append({
                                        'value': point['val'],
                                        'date': point.get('end'),
                                        'unit': unit_name,
                                        'bank': company_name
                                    })
            
            bank_stats[company_name] = bank_metrics
            
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    return all_metrics, taxonomy_stats, bank_stats

def generate_holistic_report(all_metrics, taxonomy_stats, bank_stats):
    """Generate comprehensive report of all available metrics"""
    
    print("\n" + "=" * 100)
    print("🏦 HOLISTIC SEC METRICS CATALOG - COMPLETE UNIVERSE")
    print("=" * 100)
    
    # Overall statistics
    total_unique_metrics = len(all_metrics)
    total_banks = len(bank_stats)
    
    print(f"📊 UNIVERSE OVERVIEW:")
    print(f"  • Total Unique Metrics: {total_unique_metrics:,}")
    print(f"  • Total Banks Analyzed: {total_banks}")
    print(f"  • Total Taxonomies: {len(taxonomy_stats)}")
    
    # Taxonomy breakdown
    print(f"\n📚 TAXONOMY BREAKDOWN:")
    for taxonomy, stats in sorted(taxonomy_stats.items()):
        unique_metrics = len(stats['metrics'])
        bank_count = len(stats['banks'])
        print(f"  • {taxonomy:15} | {unique_metrics:4d} unique metrics | Used by {bank_count:2d} banks")
    
    # Most common metrics across banks
    print(f"\n🔝 MOST COMMON METRICS (Found in Most Banks):")
    common_metrics = sorted(all_metrics.items(), key=lambda x: x[1]['count'], reverse=True)
    for i, (metric_name, data) in enumerate(common_metrics[:20], 1):
        bank_count = len(data['banks'])
        taxonomies = ", ".join(sorted(data['taxonomies']))
        labels = list(data['labels'])
        label = labels[0] if labels else "No label"
        label_text = (label[:50] if label else "No label")
        print(f"  {i:2d}. {metric_name:50} | {bank_count:2d} banks | {taxonomies:15} | {label_text}")
    
    # Bank-specific analysis
    print(f"\n🏛️ BANK-SPECIFIC METRICS RICHNESS:")
    bank_richness = [(name, stats['total_metrics'], stats['total_data_points']) 
                     for name, stats in bank_stats.items()]
    bank_richness.sort(key=lambda x: x[1], reverse=True)
    
    print(f"{'Bank Name':45} | {'Metrics':8} | {'Data Points':12} | {'Taxonomies'}")
    print("-" * 85)
    for name, metrics, data_points, in bank_richness:
        taxonomies = len(bank_stats[name]['taxonomies'])
        print(f"{name[:44]:44} | {metrics:8,} | {data_points:12,} | {taxonomies}")
    
    return {
        'total_metrics': total_unique_metrics,
        'total_banks': total_banks,
        'taxonomies': dict(taxonomy_stats),
        'common_metrics': dict(common_metrics[:50]),  # Top 50
        'bank_stats': bank_stats
    }

def main():
    print("🔍 Building Holistic SEC Metrics Catalog...")
    print("This will analyze ALL metrics in ALL raw JSON files")
    print("=" * 80)
    
    # Analyze all raw JSON files
    all_metrics, taxonomy_stats, bank_stats = analyze_raw_json_structure()
    
    # Generate comprehensive report
    holistic_data = generate_holistic_report(all_metrics, taxonomy_stats, bank_stats)
    
    print(f"\n💾 Analysis complete!")
    print(f"📊 Universe contains {len(all_metrics):,} unique metrics across {len(bank_stats)} banks")

if __name__ == "__main__":
    main()
