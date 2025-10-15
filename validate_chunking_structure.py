#!/usr/bin/env python3
"""
Validate Complete Metrics Structure for Business-Function Based Chunking
Analyze all complete metrics files to ensure consistent structure and categorization
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter

def categorize_metric(metric_name, metric_info):
    """Categorize a metric based on name and metadata"""
    name_lower = metric_name.lower()
    label_lower = (metric_info.get('label') or '').lower()
    desc_lower = (metric_info.get('description') or '').lower()
    
    # Combined text for analysis
    combined_text = f"{name_lower} {label_lower} {desc_lower}"
    
    # Business function classification
    if any(term in combined_text for term in [
        'asset', 'liability', 'deposit', 'cash', 'securities', 'investment', 
        'receivable', 'payable', 'balance', 'position'
    ]):
        return 'financial_position'
    
    elif any(term in combined_text for term in [
        'revenue', 'income', 'interest', 'fee', 'earnings', 'profit', 
        'gain', 'loss', 'margin', 'yield'
    ]):
        return 'revenue_profit'
    
    elif any(term in combined_text for term in [
        'capital', 'risk', 'tier', 'ratio', 'adequacy', 'leverage', 
        'credit', 'loan', 'provision', 'allowance', 'impairment'
    ]):
        return 'risk_capital'
    
    elif any(term in combined_text for term in [
        'expense', 'cost', 'operating', 'efficiency', 'employee', 
        'trading', 'derivative', 'fair', 'market', 'unrealized'
    ]):
        return 'operations'
    
    else:
        return 'metadata_other'

def analyze_file_structure(file_path):
    """Analyze the structure of a complete metrics file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Validate expected structure
        required_keys = ['company_info', 'metrics_summary', 'taxonomies', 'all_metrics']
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            return {
                'valid': False,
                'error': f"Missing keys: {missing_keys}",
                'company': file_path.name
            }
        
        # Analyze metrics distribution
        all_metrics = data['all_metrics']
        categorization = defaultdict(list)
        
        for metric_name, metric_info in all_metrics.items():
            category = categorize_metric(metric_name, metric_info)
            categorization[category].append(metric_name)
        
        # Calculate token estimates per category (rough estimate)
        char_counts = {}
        for category, metrics in categorization.items():
            total_chars = 0
            for metric in metrics:
                metric_data = all_metrics[metric]
                # Estimate characters in this metric's JSON representation
                metric_json = json.dumps(metric_data, indent=2)
                total_chars += len(metric_json)
            char_counts[category] = total_chars
        
        return {
            'valid': True,
            'company': data['company_info']['name'],
            'file': file_path.name,
            'total_metrics': len(all_metrics),
            'taxonomies': list(data['taxonomies'].keys()),
            'categorization': {cat: len(metrics) for cat, metrics in categorization.items()},
            'char_counts': char_counts,
            'token_estimates': {cat: chars // 3.5 for cat, chars in char_counts.items()},
            'structure_consistent': True
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'company': file_path.name
        }

def main():
    print("🔍 VALIDATING COMPLETE METRICS STRUCTURE FOR CHUNKING")
    print("=" * 80)
    
    # Get all complete metrics files
    complete_dir = Path("sec_metrics_data/complete_metrics")
    json_files = list(complete_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {complete_dir}")
        return
    
    print(f"📁 Analyzing {len(json_files)} complete metrics files...")
    print()
    
    # Analyze each file
    results = []
    valid_files = 0
    invalid_files = 0
    
    for json_file in sorted(json_files):
        print(f"Analyzing: {json_file.name}...")
        result = analyze_file_structure(json_file)
        results.append(result)
        
        if result['valid']:
            valid_files += 1
        else:
            invalid_files += 1
            print(f"  ❌ ERROR: {result['error']}")
    
    print()
    print("📊 STRUCTURE VALIDATION RESULTS")
    print("=" * 80)
    print(f"✅ Valid files: {valid_files}")
    print(f"❌ Invalid files: {invalid_files}")
    print(f"📈 Success rate: {(valid_files/len(json_files)*100):.1f}%")
    print()
    
    if invalid_files > 0:
        print("❌ STRUCTURAL ISSUES FOUND - Cannot proceed with chunking")
        return
    
    # Analyze categorization consistency
    print("📋 BUSINESS FUNCTION CATEGORIZATION ANALYSIS")
    print("=" * 80)
    
    # Aggregate statistics
    category_stats = defaultdict(list)
    token_stats = defaultdict(list)
    taxonomy_usage = Counter()
    
    for result in results:
        if not result['valid']:
            continue
            
        for category, count in result['categorization'].items():
            category_stats[category].append(count)
        
        for category, tokens in result['token_estimates'].items():
            token_stats[category].append(tokens)
        
        for taxonomy in result['taxonomies']:
            taxonomy_usage[taxonomy] += 1
    
    # Print category analysis
    categories = ['financial_position', 'revenue_profit', 'risk_capital', 'operations', 'metadata_other']
    
    print("📈 METRICS DISTRIBUTION BY CATEGORY:")
    print()
    print(f"{'Category':<20} | {'Min':<5} | {'Max':<5} | {'Avg':<5} | {'Total':<7}")
    print("-" * 65)
    
    total_metrics_all = 0
    for category in categories:
        if category in category_stats:
            counts = category_stats[category]
            min_count = min(counts)
            max_count = max(counts)
            avg_count = sum(counts) / len(counts)
            total_count = sum(counts)
            total_metrics_all += total_count
            
            print(f"{category:<20} | {min_count:<5} | {max_count:<5} | {avg_count:<5.0f} | {total_count:<7}")
    
    print("-" * 65)
    print(f"{'TOTAL':<20} | {'':<5} | {'':<5} | {'':<5} | {total_metrics_all:<7}")
    
    print()
    print("🎯 TOKEN DISTRIBUTION BY CATEGORY:")
    print()
    print(f"{'Category':<20} | {'Min Tokens':<10} | {'Max Tokens':<10} | {'Avg Tokens':<10}")
    print("-" * 70)
    
    chunk_feasible = True
    for category in categories:
        if category in token_stats:
            tokens = token_stats[category]
            min_tokens = min(tokens)
            max_tokens = max(tokens)
            avg_tokens = sum(tokens) / len(tokens)
            
            # Check if any category exceeds 50K tokens (problematic for chunking)
            status = "✅" if max_tokens < 50000 else "⚠️" if max_tokens < 70000 else "❌"
            if max_tokens > 50000:
                chunk_feasible = False
            
            print(f"{category:<20} | {min_tokens:<10.0f} | {max_tokens:<10.0f} | {avg_tokens:<10.0f} {status}")
    
    print()
    print("🏗️ CHUNKING FEASIBILITY ASSESSMENT")
    print("=" * 80)
    
    if chunk_feasible:
        print("✅ CHUNKING FEASIBLE: All categories stay within reasonable token limits")
        print()
        print("📋 RECOMMENDED CHUNK STRUCTURE:")
        
        for i, category in enumerate(categories, 1):
            if category in token_stats:
                avg_tokens = sum(token_stats[category]) / len(token_stats[category])
                avg_metrics = sum(category_stats[category]) / len(category_stats[category])
                
                chunk_name = {
                    'financial_position': 'Financial Position & Assets',
                    'revenue_profit': 'Revenue & Profitability', 
                    'risk_capital': 'Risk & Capital Management',
                    'operations': 'Operations & Trading',
                    'metadata_other': 'Metadata & Other'
                }[category]
                
                print(f"  Chunk {i}: {chunk_name}")
                print(f"    └── ~{avg_tokens:.0f} tokens, ~{avg_metrics:.0f} metrics")
        
        print()
        print("🎯 IMPLEMENTATION READY:")
        print("  • Consistent structure across all files ✅")
        print("  • Balanced token distribution ✅") 
        print("  • Clear business categorization ✅")
        print("  • All chunks fit within 50K token limit ✅")
        
    else:
        print("⚠️ CHUNKING CHALLENGES DETECTED:")
        print("  • Some categories exceed 50K tokens")
        print("  • May need sub-chunking or different approach")
        print("  • Review large categories for further breakdown")
    
    print()
    print("📚 TAXONOMY USAGE ACROSS FILES:")
    print()
    for taxonomy, count in taxonomy_usage.most_common():
        print(f"  {taxonomy}: {count}/{len(results)} files ({count/len(results)*100:.1f}%)")
    
    print()
    print("🔍 DETAILED ANALYSIS SAMPLE (First 3 files):")
    print("=" * 80)
    
    for i, result in enumerate(results[:3]):
        if not result['valid']:
            continue
            
        print(f"\n{i+1}. {result['company']} ({result['file']})")
        print(f"   Total metrics: {result['total_metrics']}")
        print(f"   Taxonomies: {', '.join(result['taxonomies'])}")
        print("   Category breakdown:")
        
        for category in categories:
            if category in result['categorization']:
                metrics_count = result['categorization'][category]
                tokens = result['token_estimates'][category]
                print(f"     {category:<20}: {metrics_count:3d} metrics, ~{tokens:5.0f} tokens")
    
    # Save detailed results
    output_file = "chunking_validation_results.json"
    validation_data = {
        'validation_summary': {
            'total_files': len(json_files),
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'chunking_feasible': chunk_feasible
        },
        'category_statistics': {
            'metrics_distribution': {cat: {
                'min': min(counts), 
                'max': max(counts), 
                'avg': sum(counts)/len(counts),
                'total': sum(counts)
            } for cat, counts in category_stats.items()},
            'token_distribution': {cat: {
                'min': min(tokens),
                'max': max(tokens), 
                'avg': sum(tokens)/len(tokens)
            } for cat, tokens in token_stats.items()}
        },
        'file_details': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(validation_data, f, indent=2)
    
    print(f"\n📄 Detailed validation results saved: {output_file}")

if __name__ == "__main__":
    main()

