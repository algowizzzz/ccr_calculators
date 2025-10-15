#!/usr/bin/env python3
"""
Analyze token counts for all raw JSON files in sec_metrics_data/raw_json/
"""

import json
from pathlib import Path
import statistics

def estimate_tokens_advanced(text):
    """Advanced token estimation for JSON: ~3.5 characters per token"""
    return len(text) / 3.5

def analyze_raw_json_tokens():
    raw_json_dir = Path("sec_metrics_data/raw_json")
    
    if not raw_json_dir.exists():
        print("❌ raw_json directory not found")
        return
    
    json_files = list(raw_json_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found in raw_json directory")
        return
    
    print(f"📊 Analyzing {len(json_files)} raw JSON files...")
    print("=" * 80)
    
    token_counts = []
    file_sizes = []
    company_data = []
    
    for json_file in sorted(json_files):
        try:
            # Get file size
            file_size = json_file.stat().st_size
            file_sizes.append(file_size)
            
            # Read and analyze content
            with open(json_file, 'r') as f:
                content = f.read()
            
            # Calculate tokens
            char_count = len(content)
            token_estimate = estimate_tokens_advanced(content)
            token_counts.append(token_estimate)
            
            # Try to get company name
            try:
                json_data = json.loads(content)
                company_name = json_data.get('entityName', 'Unknown')
                cik = json_data.get('cik', 'Unknown')
            except:
                company_name = 'Parse Error'
                cik = 'Unknown'
            
            company_data.append({
                'file': json_file.name,
                'company': company_name,
                'cik': cik,
                'size_mb': file_size / (1024 * 1024),
                'chars': char_count,
                'tokens': int(token_estimate)
            })
            
            print(f"{json_file.name[:30]:30} | {company_name[:35]:35} | {file_size/1024/1024:6.1f} MB | {int(token_estimate):8,} tokens")
            
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    if not token_counts:
        print("❌ No files successfully processed")
        return
    
    # Calculate statistics
    avg_tokens = statistics.mean(token_counts)
    median_tokens = statistics.median(token_counts)
    min_tokens = min(token_counts)
    max_tokens = max(token_counts)
    std_tokens = statistics.stdev(token_counts) if len(token_counts) > 1 else 0
    
    avg_size = statistics.mean(file_sizes)
    total_size = sum(file_sizes)
    total_tokens = sum(token_counts)
    
    print("\n" + "=" * 80)
    print("📈 TOKEN COUNT STATISTICS")
    print("=" * 80)
    print(f"Total files analyzed: {len(json_files)}")
    print(f"Total size: {total_size/(1024*1024):.1f} MB")
    print(f"Total tokens: {int(total_tokens):,}")
    print()
    print(f"Average tokens per file: {int(avg_tokens):,}")
    print(f"Median tokens per file: {int(median_tokens):,}")
    print(f"Min tokens: {int(min_tokens):,}")
    print(f"Max tokens: {int(max_tokens):,}")
    print(f"Standard deviation: {int(std_tokens):,}")
    print()
    print(f"Average file size: {avg_size/(1024*1024):.1f} MB")
    
    # Token size categories
    small_files = [c for c in company_data if c['tokens'] < 50000]
    medium_files = [c for c in company_data if 50000 <= c['tokens'] < 150000]
    large_files = [c for c in company_data if 150000 <= c['tokens'] < 300000]
    xlarge_files = [c for c in company_data if c['tokens'] >= 300000]
    
    print(f"\n📊 SIZE DISTRIBUTION:")
    print(f"Small files (< 50K tokens): {len(small_files)}")
    print(f"Medium files (50K-150K tokens): {len(medium_files)}")
    print(f"Large files (150K-300K tokens): {len(large_files)}")
    print(f"X-Large files (≥ 300K tokens): {len(xlarge_files)}")
    
    # Show largest files
    print(f"\n🔝 TOP 5 LARGEST FILES:")
    sorted_by_tokens = sorted(company_data, key=lambda x: x['tokens'], reverse=True)
    for i, company in enumerate(sorted_by_tokens[:5], 1):
        print(f"{i}. {company['company'][:40]:40} | {company['tokens']:,} tokens | {company['size_mb']:.1f} MB")
    
    # Show smallest files
    print(f"\n🔻 TOP 5 SMALLEST FILES:")
    for i, company in enumerate(sorted_by_tokens[-5:], 1):
        print(f"{i}. {company['company'][:40]:40} | {company['tokens']:,} tokens | {company['size_mb']:.1f} MB")
    
    return {
        'total_files': len(json_files),
        'avg_tokens': int(avg_tokens),
        'median_tokens': int(median_tokens),
        'min_tokens': int(min_tokens),
        'max_tokens': int(max_tokens),
        'total_tokens': int(total_tokens),
        'total_size_mb': total_size/(1024*1024),
        'company_data': company_data
    }

if __name__ == "__main__":
    results = analyze_raw_json_tokens()
    
    if results:
        # Save detailed analysis
        with open('sec_metrics_data/token_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed analysis saved: sec_metrics_data/token_analysis.json")

