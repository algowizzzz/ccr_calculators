#!/usr/bin/env python3
"""
Gap Analysis: Chunked Metrics vs Raw JSON for Bank of America
Verify completeness of chunking process and identify any missing data
"""

import json
from pathlib import Path
from collections import defaultdict

def load_raw_json():
    """Load Bank of America raw JSON data"""
    raw_file = Path("sec_metrics_data/raw_json/companyfacts_0000070858.json")
    with open(raw_file, 'r') as f:
        return json.load(f)

def load_complete_metrics():
    """Load Bank of America complete metrics data"""
    complete_file = Path("sec_metrics_data/complete_metrics/Bank_of_America_Corporation_all_metrics.json")
    with open(complete_file, 'r') as f:
        return json.load(f)

def load_chunked_metrics():
    """Load all Bank of America chunk files"""
    chunks_dir = Path("sec_metrics_data/chunked_metrics")
    bac_chunks = list(chunks_dir.glob("public_BAC_70858_SEC_*.json"))
    
    chunked_data = {}
    total_chunked_metrics = {}
    
    for chunk_file in bac_chunks:
        with open(chunk_file, 'r') as f:
            chunk_data = json.load(f)
            
        chunk_name = chunk_data['chunk_metadata']['chunk_name']
        chunk_id = chunk_data['chunk_metadata']['chunk_id']
        metrics = chunk_data['metrics']
        
        chunked_data[chunk_id] = {
            'name': chunk_name,
            'metrics_count': len(metrics),
            'metrics': metrics
        }
        
        # Add to total metrics
        total_chunked_metrics.update(metrics)
    
    return chunked_data, total_chunked_metrics

def analyze_raw_structure(raw_data):
    """Analyze the structure of raw JSON data"""
    facts = raw_data.get('facts', {})
    
    raw_analysis = {
        'company_name': raw_data.get('entityName', 'Unknown'),
        'cik': raw_data.get('cik', 'Unknown'),
        'taxonomies': {},
        'total_metrics': 0,
        'all_metrics': {}
    }
    
    for taxonomy, taxonomy_data in facts.items():
        metric_count = len(taxonomy_data)
        raw_analysis['taxonomies'][taxonomy] = {
            'metrics_count': metric_count,
            'metrics': list(taxonomy_data.keys())
        }
        raw_analysis['total_metrics'] += metric_count
        
        # Store all metrics with taxonomy info
        for metric_name, metric_data in taxonomy_data.items():
            raw_analysis['all_metrics'][metric_name] = {
                'taxonomy': taxonomy,
                'label': metric_data.get('label'),
                'description': metric_data.get('description'),
                'units': list(metric_data.get('units', {}).keys()),
                'data_points': sum(len(unit_data) for unit_data in metric_data.get('units', {}).values())
            }
    
    return raw_analysis

def main():
    print("🔍 GAP ANALYSIS: Chunked Metrics vs Raw JSON (Bank of America)")
    print("=" * 80)
    
    # Load all data sources
    print("Loading data sources...")
    raw_data = load_raw_json()
    complete_data = load_complete_metrics()
    chunked_data, total_chunked_metrics = load_chunked_metrics()
    
    # Analyze raw structure
    raw_analysis = analyze_raw_structure(raw_data)
    
    print(f"✅ Raw JSON loaded: {raw_analysis['total_metrics']} metrics")
    print(f"✅ Complete metrics loaded: {len(complete_data['all_metrics'])} metrics")
    print(f"✅ Chunked metrics loaded: {len(total_chunked_metrics)} metrics across {len(chunked_data)} chunks")
    print()
    
    # Data completeness analysis
    print("📊 DATA COMPLETENESS ANALYSIS")
    print("=" * 80)
    
    raw_metrics = set(raw_analysis['all_metrics'].keys())
    complete_metrics = set(complete_data['all_metrics'].keys())
    chunked_metrics = set(total_chunked_metrics.keys())
    
    print(f"📈 Raw JSON metrics: {len(raw_metrics):,}")
    print(f"📈 Complete metrics: {len(complete_metrics):,}")
    print(f"📈 Chunked metrics: {len(chunked_metrics):,}")
    print()
    
    # Check Raw -> Complete completeness
    missing_in_complete = raw_metrics - complete_metrics
    extra_in_complete = complete_metrics - raw_metrics
    
    print("🔍 RAW JSON → COMPLETE METRICS COMPARISON:")
    print(f"  Missing in complete: {len(missing_in_complete)} metrics")
    print(f"  Extra in complete: {len(extra_in_complete)} metrics")
    print(f"  Completeness rate: {(len(complete_metrics & raw_metrics) / len(raw_metrics) * 100):.2f}%")
    
    if missing_in_complete:
        print(f"  ❌ Missing metrics (first 5): {list(missing_in_complete)[:5]}")
    if extra_in_complete:
        print(f"  ➕ Extra metrics (first 5): {list(extra_in_complete)[:5]}")
    print()
    
    # Check Complete -> Chunked completeness
    missing_in_chunked = complete_metrics - chunked_metrics
    extra_in_chunked = chunked_metrics - complete_metrics
    
    print("🔍 COMPLETE METRICS → CHUNKED METRICS COMPARISON:")
    print(f"  Missing in chunks: {len(missing_in_chunked)} metrics")
    print(f"  Extra in chunks: {len(extra_in_chunked)} metrics")
    print(f"  Completeness rate: {(len(chunked_metrics & complete_metrics) / len(complete_metrics) * 100):.2f}%")
    
    if missing_in_chunked:
        print(f"  ❌ Missing metrics (first 10):")
        for i, metric in enumerate(list(missing_in_chunked)[:10], 1):
            print(f"    {i:2d}. {metric}")
    
    if extra_in_chunked:
        print(f"  ➕ Extra metrics: {list(extra_in_chunked)[:5]}")
    print()
    
    # Taxonomy distribution analysis
    print("📚 TAXONOMY DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Raw taxonomy distribution
    print("Raw JSON taxonomies:")
    for taxonomy, info in raw_analysis['taxonomies'].items():
        print(f"  {taxonomy}: {info['metrics_count']} metrics")
    print()
    
    # Complete metrics taxonomy distribution
    complete_taxonomies = defaultdict(int)
    for metric_info in complete_data['all_metrics'].values():
        taxonomy = metric_info.get('taxonomy', 'unknown')
        complete_taxonomies[taxonomy] += 1
    
    print("Complete metrics taxonomies:")
    for taxonomy, count in complete_taxonomies.items():
        print(f"  {taxonomy}: {count} metrics")
    print()
    
    # Chunked metrics distribution
    print("Chunked metrics distribution:")
    for chunk_id, chunk_info in chunked_data.items():
        print(f"  {chunk_info['name']}: {chunk_info['metrics_count']} metrics")
    
    total_chunked = sum(chunk_info['metrics_count'] for chunk_info in chunked_data.values())
    print(f"  TOTAL: {total_chunked} metrics")
    print()
    
    # Data integrity checks
    print("🔒 DATA INTEGRITY CHECKS")
    print("=" * 80)
    
    # Check if any metrics appear in multiple chunks
    all_chunk_metrics = []
    chunk_assignments = defaultdict(list)
    
    for chunk_id, chunk_info in chunked_data.items():
        for metric_name in chunk_info['metrics'].keys():
            all_chunk_metrics.append(metric_name)
            chunk_assignments[metric_name].append(chunk_info['name'])
    
    duplicates = {metric: chunks for metric, chunks in chunk_assignments.items() if len(chunks) > 1}
    
    if duplicates:
        print(f"❌ DUPLICATE METRICS FOUND: {len(duplicates)} metrics appear in multiple chunks")
        for metric, chunks in list(duplicates.items())[:5]:
            print(f"  {metric}: {', '.join(chunks)}")
    else:
        print("✅ No duplicate metrics found - each metric appears in exactly one chunk")
    print()
    
    # Sample data validation - check if metric content is preserved
    print("🔍 SAMPLE DATA VALIDATION")
    print("=" * 80)
    
    sample_metrics = list(chunked_metrics)[:3]
    
    for metric_name in sample_metrics:
        # Get from raw
        raw_metric = None
        for taxonomy_data in raw_data['facts'].values():
            if metric_name in taxonomy_data:
                raw_metric = taxonomy_data[metric_name]
                break
        
        # Get from complete
        complete_metric = complete_data['all_metrics'].get(metric_name)
        
        # Get from chunks
        chunked_metric = total_chunked_metrics.get(metric_name)
        
        print(f"📊 Metric: {metric_name}")
        print(f"  Raw JSON: {'✅ Found' if raw_metric else '❌ Missing'}")
        print(f"  Complete: {'✅ Found' if complete_metric else '❌ Missing'}")
        print(f"  Chunked:  {'✅ Found' if chunked_metric else '❌ Missing'}")
        
        if raw_metric and complete_metric and chunked_metric:
            # Check data consistency
            raw_units = list(raw_metric.get('units', {}).keys())
            complete_units = complete_metric.get('available_units', [])
            chunked_units = chunked_metric.get('available_units', [])
            
            units_match = set(raw_units) == set(complete_units) == set(chunked_units)
            print(f"  Units consistency: {'✅' if units_match else '❌'}")
            
            if not units_match:
                print(f"    Raw: {raw_units}")
                print(f"    Complete: {complete_units}")
                print(f"    Chunked: {chunked_units}")
        print()
    
    # Summary
    print("📋 SUMMARY")
    print("=" * 80)
    
    raw_to_complete_loss = len(missing_in_complete)
    complete_to_chunked_loss = len(missing_in_chunked)
    total_loss = len(raw_metrics) - len(chunked_metrics)
    
    print(f"🎯 Data Flow Analysis:")
    print(f"  Raw JSON → Complete: Lost {raw_to_complete_loss} metrics")
    print(f"  Complete → Chunked: Lost {complete_to_chunked_loss} metrics")
    print(f"  Overall: Lost {total_loss} metrics ({(total_loss/len(raw_metrics)*100):.2f}%)")
    print()
    
    if total_loss == 0:
        print("✅ PERFECT DATA PRESERVATION: No metrics lost in processing pipeline")
    elif total_loss < 10:
        print("✅ EXCELLENT DATA PRESERVATION: Minimal data loss")
    elif total_loss < 50:
        print("⚠️ GOOD DATA PRESERVATION: Some data loss detected")
    else:
        print("❌ SIGNIFICANT DATA LOSS: Investigation required")
    
    print()
    print("🎯 Chunking Quality:")
    if len(duplicates) == 0:
        print("✅ Perfect chunk separation - no overlapping metrics")
    else:
        print(f"⚠️ {len(duplicates)} metrics appear in multiple chunks")
    
    chunk_balance = [chunk_info['metrics_count'] for chunk_info in chunked_data.values()]
    min_chunk = min(chunk_balance)
    max_chunk = max(chunk_balance)
    balance_ratio = max_chunk / min_chunk if min_chunk > 0 else float('inf')
    
    print(f"📊 Chunk balance: {min_chunk}-{max_chunk} metrics per chunk (ratio: {balance_ratio:.1f}:1)")
    
    if balance_ratio < 10:
        print("✅ Well-balanced chunks")
    elif balance_ratio < 20:
        print("⚠️ Moderately unbalanced chunks")
    else:
        print("❌ Highly unbalanced chunks - consider rebalancing")

if __name__ == "__main__":
    main()

