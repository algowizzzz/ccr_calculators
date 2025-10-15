#!/usr/bin/env python3
"""
Analyze token counts for all complete metrics JSON files.
Calculate min, max, average, median, and standard deviation.
"""

import json
import sys
from pathlib import Path
import statistics

def count_tokens(file_path):
    """Calculate token count for a JSON file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        char_count = len(content)
        word_count = len(content.split())
        line_count = content.count('\n') + 1
        
        # Token estimates based on common ratios
        simple_tokens = char_count / 4
        word_based_tokens = word_count * 0.75
        advanced_tokens = char_count / 3.5  # More accurate for JSON/code
        
        # Use advanced estimate as primary
        estimated_tokens = int(advanced_tokens)
        
        return {
            'file': file_path.name,
            'char_count': char_count,
            'word_count': word_count,
            'line_count': line_count,
            'tokens': estimated_tokens,
            'size_mb': char_count / (1024 * 1024)
        }
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return None

def main():
    # Directory containing complete metrics files
    metrics_dir = Path("sec_metrics_data/complete_metrics")
    
    if not metrics_dir.exists():
        print(f"❌ Directory not found: {metrics_dir}")
        return
    
    # Get all JSON files
    json_files = list(metrics_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {metrics_dir}")
        return
    
    print(f"🔍 Analyzing token counts for {len(json_files)} complete metrics files...")
    print("=" * 80)
    
    # Process all files
    results = []
    failed = 0
    
    for json_file in sorted(json_files):
        result = count_tokens(json_file)
        if result:
            results.append(result)
        else:
            failed += 1
    
    if not results:
        print("❌ No files processed successfully")
        return
    
    # Calculate statistics
    token_counts = [r['tokens'] for r in results]
    char_counts = [r['char_count'] for r in results]
    file_sizes = [r['size_mb'] for r in results]
    
    min_tokens = min(token_counts)
    max_tokens = max(token_counts)
    avg_tokens = statistics.mean(token_counts)
    median_tokens = statistics.median(token_counts)
    stdev_tokens = statistics.stdev(token_counts) if len(token_counts) > 1 else 0
    
    # Find min/max files
    min_file = next(r for r in results if r['tokens'] == min_tokens)
    max_file = next(r for r in results if r['tokens'] == max_tokens)
    
    # Print summary statistics
    print("📊 TOKEN COUNT ANALYSIS - COMPLETE METRICS FILES")
    print("=" * 80)
    print(f"📁 Files analyzed: {len(results)}")
    print(f"❌ Files failed: {failed}")
    print()
    
    print("🎯 TOKEN STATISTICS:")
    print(f"  Minimum:     {min_tokens:,} tokens ({min_file['file']})")
    print(f"  Maximum:     {max_tokens:,} tokens ({max_file['file']})")
    print(f"  Average:     {avg_tokens:,.0f} tokens")
    print(f"  Median:      {median_tokens:,.0f} tokens")
    print(f"  Std Dev:     {stdev_tokens:,.0f} tokens")
    print()
    
    print("📏 FILE SIZE STATISTICS:")
    print(f"  Minimum:     {min(file_sizes):.2f} MB")
    print(f"  Maximum:     {max(file_sizes):.2f} MB") 
    print(f"  Average:     {statistics.mean(file_sizes):.2f} MB")
    print(f"  Total:       {sum(file_sizes):.2f} MB")
    print()
    
    print("📈 CHARACTER COUNT STATISTICS:")
    print(f"  Minimum:     {min(char_counts):,} chars")
    print(f"  Maximum:     {max(char_counts):,} chars")
    print(f"  Average:     {statistics.mean(char_counts):,.0f} chars")
    print(f"  Total:       {sum(char_counts):,} chars")
    print()
    
    # Show token distribution
    print("📊 TOKEN DISTRIBUTION:")
    ranges = [
        (0, 50000, "Small"),
        (50000, 100000, "Medium"), 
        (100000, 200000, "Large"),
        (200000, 300000, "Very Large"),
        (300000, float('inf'), "Extremely Large")
    ]
    
    for min_range, max_range, label in ranges:
        count = len([t for t in token_counts if min_range <= t < max_range])
        if count > 0:
            percentage = (count / len(token_counts)) * 100
            print(f"  {label:15}: {count:2d} files ({percentage:4.1f}%)")
    
    print()
    
    # Show top 5 largest and smallest files
    sorted_results = sorted(results, key=lambda x: x['tokens'])
    
    print("🔝 TOP 5 LARGEST FILES:")
    for i, result in enumerate(sorted_results[-5:][::-1], 1):
        print(f"  {i}. {result['file'][:50]:50} | {result['tokens']:,} tokens | {result['size_mb']:.2f} MB")
    
    print()
    print("🔻 TOP 5 SMALLEST FILES:")
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {result['file'][:50]:50} | {result['tokens']:,} tokens | {result['size_mb']:.2f} MB")
    
    print()
    print("=" * 80)
    print(f"💾 Total dataset: {sum(file_sizes):.2f} MB | {sum(token_counts):,} tokens")
    
    # Save detailed results
    output_file = "complete_metrics_token_analysis.json"
    analysis_data = {
        'summary': {
            'files_analyzed': len(results),
            'files_failed': failed,
            'total_tokens': sum(token_counts),
            'total_size_mb': sum(file_sizes),
            'statistics': {
                'min_tokens': min_tokens,
                'max_tokens': max_tokens,
                'avg_tokens': round(avg_tokens),
                'median_tokens': round(median_tokens),
                'stdev_tokens': round(stdev_tokens)
            }
        },
        'file_details': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"📄 Detailed analysis saved: {output_file}")

if __name__ == "__main__":
    main()

