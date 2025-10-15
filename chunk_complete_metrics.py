#!/usr/bin/env python3
"""
Chunk Complete Metrics into Business-Function Based Categories
Creates 6 chunks per company with proper metadata structure
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def get_ticker_from_filename(filename):
    """Extract ticker from filename - simplified approach"""
    # Remove common suffixes and convert to uppercase
    name = filename.replace('_all_metrics.json', '')
    
    # Handle special cases
    ticker_mapping = {
        'JPMorgan_Chase__Co': 'JPM',
        'Bank_of_America_Corporation': 'BAC', 
        'WELLS_FARGO__COMPANYMN': 'WFC',
        'CitigroupInc': 'C',
        'MORGAN_STANLEY': 'MS',
        'The_Goldman_Sachs_Group_Inc': 'GS',
        'US_BANCORP_DE': 'USB',
        'TRUIST_FINANCIAL_CORPORATION': 'TFC',
        'PNC_Financial_Services_Group_Inc': 'PNC',
        'BANK_OF_NEW_YORK_MELLON_CORPORATION': 'BK',
        'THE_BANK_OF_NEW_YORK_MELLON_CORPORATION': 'BK',
        'STATE_STREET_CORPORATION': 'STT',
        'CAPITALONEFINANCIALCORP': 'COF',
        'CAPITAL_ONE_FINANCIAL_CORP': 'COF',
        'SCHWAB_CHARLES_CORP': 'SCHW',
        'NORTHERN_TRUST_CORPORATION': 'NTRS',
        'Fifth_Third_Bancorp': 'FITB',
        'KeyCorp': 'KEY',
        'Regions_Financial_Corporation': 'RF',
        'Huntington_Bancshares_Incorporated': 'HBAN',
        'Comerica_Incorporated': 'CMA',
        'ZIONS_BANCORPORATION_NATIONAL_ASSOCIATION': 'ZION',
        'MT_BANK_CORPORATION': 'MTB',
        'FIRST_CITIZENS_BANCSHARES_INC_DE': 'FCNCA',
        'CITIZENS_FINANCIAL_GROUP_INCRI': 'CFG',
        'Royal_Bank_of_Canada': 'RY',
        'TORONTO_DOMINION_BANK': 'TD',
        'BANK_OF_NOVA_SCOTIA': 'BNS',
        'BANK_OF_MONTREAL': 'BMO',
        'CANADIAN_IMPERIAL_BANK_OF_COMMERCE': 'CM'
    }
    
    return ticker_mapping.get(name, name[:4].upper())

def categorize_metric(metric_name, metric_info):
    """Categorize a metric into one of 6 business function chunks"""
    name_lower = metric_name.lower()
    label_lower = (metric_info.get('label') or '').lower()
    desc_lower = (metric_info.get('description') or '').lower()
    
    combined_text = f"{name_lower} {label_lower} {desc_lower}"
    
    # Chunk 1: Assets & Cash
    if any(term in combined_text for term in [
        'cash', 'securities', 'investment', 'trading', 'available', 'held', 
        'receivable', 'asset', 'equity', 'stock', 'bond', 'treasury'
    ]) and not any(term in combined_text for term in ['loan', 'credit', 'financing', 'mortgage']):
        return 'assets_cash'
    
    # Chunk 2: Liabilities & Deposits  
    elif any(term in combined_text for term in [
        'liability', 'deposit', 'payable', 'debt', 'borrowing', 'obligation', 
        'due', 'accrued', 'customer', 'demand', 'time', 'savings'
    ]):
        return 'liabilities_deposits'
    
    # Chunk 3: Loans & Credit
    elif any(term in combined_text for term in [
        'loan', 'credit', 'financing', 'mortgage', 'commercial', 'consumer', 
        'lease', 'allowance', 'provision', 'impairment', 'chargeoff', 'nonperforming'
    ]):
        return 'loans_credit'
    
    # Chunk 4: Revenue & Profitability
    elif any(term in combined_text for term in [
        'revenue', 'income', 'interest', 'fee', 'earnings', 'profit', 
        'gain', 'loss', 'margin', 'yield', 'dividend', 'commission'
    ]):
        return 'revenue_profit'
    
    # Chunk 5: Risk & Capital Management
    elif any(term in combined_text for term in [
        'capital', 'risk', 'tier', 'ratio', 'adequacy', 'leverage', 
        'regulatory', 'basel', 'rwa', 'cet1', 'buffer'
    ]):
        return 'risk_capital'
    
    # Chunk 6: Operations & Metadata (default)
    else:
        return 'operations_metadata'

def create_chunk_metadata(company_info, chunk_name, ticker, chunk_data):
    """Create standardized metadata for each chunk"""
    chunk_display_names = {
        'assets_cash': 'Assets & Cash',
        'liabilities_deposits': 'Liabilities & Deposits', 
        'loans_credit': 'Loans & Credit',
        'revenue_profit': 'Revenue & Profitability',
        'risk_capital': 'Risk & Capital Management',
        'operations_metadata': 'Operations & Metadata'
    }
    
    return {
        'domain': 'public',
        'CIK': company_info.get('cik', 'Unknown'),
        'data_type': 'SEC',
        'ticker': ticker,
        'chunk_name': chunk_display_names.get(chunk_name, chunk_name),
        'chunk_id': chunk_name,
        'company_name': company_info.get('name', 'Unknown'),
        'extraction_date': datetime.now().isoformat(),
        'metrics_count': len(chunk_data),
        'total_company_metrics': company_info.get('total_metrics', 0)
    }

def chunk_complete_metrics(input_file, output_dir):
    """Chunk a single complete metrics file into 6 business function chunks"""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        company_info = data['company_info']
        all_metrics = data['all_metrics']
        ticker = get_ticker_from_filename(input_file.name)
        
        # Categorize all metrics
        chunks = defaultdict(dict)
        
        for metric_name, metric_info in all_metrics.items():
            category = categorize_metric(metric_name, metric_info)
            chunks[category][metric_name] = metric_info
        
        # Create chunk files
        chunk_files = []
        
        for chunk_name, chunk_metrics in chunks.items():
            if not chunk_metrics:  # Skip empty chunks
                continue
                
            # Create chunk data structure
            chunk_data = {
                'chunk_metadata': create_chunk_metadata(company_info, chunk_name, ticker, chunk_metrics),
                'metrics': chunk_metrics
            }
            
            # Create filename: domain_ticker_CIK_datatype_chunkname.json
            cik = company_info.get('cik', '0000000000')
            filename = f"public_{ticker}_{cik}_SEC_{chunk_name}.json"
            chunk_file = output_dir / filename
            
            # Save chunk
            with open(chunk_file, 'w') as f:
                json.dump(chunk_data, f, indent=2, default=str)
            
            chunk_files.append({
                'file': filename,
                'chunk_name': chunk_name,
                'metrics_count': len(chunk_metrics),
                'estimated_tokens': sum(len(json.dumps(m, indent=2)) for m in chunk_metrics.values()) // 3.5
            })
        
        return {
            'success': True,
            'company': company_info.get('name'),
            'ticker': ticker,
            'cik': company_info.get('cik'),
            'total_metrics': len(all_metrics),
            'chunks_created': len(chunk_files),
            'chunk_details': chunk_files
        }
        
    except Exception as e:
        return {
            'success': False,
            'file': input_file.name,
            'error': str(e)
        }

def main():
    print("🔧 CHUNKING COMPLETE METRICS INTO BUSINESS FUNCTIONS")
    print("=" * 80)
    
    # Setup directories
    input_dir = Path("sec_metrics_data/complete_metrics")
    output_dir = Path("sec_metrics_data/chunked_metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all complete metrics files
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {input_dir}")
        return
    
    print(f"📁 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Processing {len(json_files)} complete metrics files...")
    print()
    
    # Process each file
    results = []
    successful = 0
    failed = 0
    total_chunks = 0
    
    for i, json_file in enumerate(sorted(json_files), 1):
        print(f"[{i}/{len(json_files)}] Processing {json_file.name}...")
        
        result = chunk_complete_metrics(json_file, output_dir)
        results.append(result)
        
        if result['success']:
            successful += 1
            total_chunks += result['chunks_created']
            print(f"  ✅ Success: {result['chunks_created']} chunks created")
            
            # Show chunk breakdown
            for chunk_detail in result['chunk_details']:
                print(f"    └── {chunk_detail['chunk_name']}: {chunk_detail['metrics_count']} metrics, ~{chunk_detail['estimated_tokens']:.0f} tokens")
        else:
            failed += 1
            print(f"  ❌ Failed: {result['error']}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("🎉 CHUNKING COMPLETE")
    print("=" * 80)
    print(f"📊 Files processed: {len(json_files)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {(successful/len(json_files)*100):.1f}%")
    print(f"📦 Total chunks created: {total_chunks}")
    print(f"📦 Average chunks per company: {total_chunks/successful:.1f}" if successful > 0 else "N/A")
    print()
    
    # Chunk distribution analysis
    chunk_stats = defaultdict(list)
    token_stats = defaultdict(list)
    
    for result in results:
        if not result['success']:
            continue
            
        for chunk_detail in result['chunk_details']:
            chunk_name = chunk_detail['chunk_name']
            chunk_stats[chunk_name].append(chunk_detail['metrics_count'])
            token_stats[chunk_name].append(chunk_detail['estimated_tokens'])
    
    print("📊 CHUNK DISTRIBUTION ANALYSIS:")
    print()
    print(f"{'Chunk Type':<25} | {'Companies':<9} | {'Avg Metrics':<12} | {'Avg Tokens':<11}")
    print("-" * 75)
    
    for chunk_name in ['Assets & Cash', 'Liabilities & Deposits', 'Loans & Credit', 
                       'Revenue & Profitability', 'Risk & Capital Management', 'Operations & Metadata']:
        if chunk_name in chunk_stats:
            companies = len(chunk_stats[chunk_name])
            avg_metrics = sum(chunk_stats[chunk_name]) / len(chunk_stats[chunk_name])
            avg_tokens = sum(token_stats[chunk_name]) / len(token_stats[chunk_name])
            
            print(f"{chunk_name:<25} | {companies:<9} | {avg_metrics:<12.0f} | {avg_tokens:<11.0f}")
    
    print()
    print("🔍 VALIDATION CHECKS:")
    print()
    
    # Check for consistent chunk counts
    chunk_counts = [r['chunks_created'] for r in results if r['success']]
    if chunk_counts:
        min_chunks = min(chunk_counts)
        max_chunks = max(chunk_counts)
        print(f"✅ Chunk count consistency: {min_chunks}-{max_chunks} chunks per company")
        
        if min_chunks != max_chunks:
            print("⚠️  Note: Some companies have different chunk counts (likely due to missing categories)")
    
    # Check token limits
    max_tokens_per_chunk = {}
    for result in results:
        if not result['success']:
            continue
        for chunk_detail in result['chunk_details']:
            chunk_name = chunk_detail['chunk_name']
            tokens = chunk_detail['estimated_tokens']
            if chunk_name not in max_tokens_per_chunk or tokens > max_tokens_per_chunk[chunk_name]:
                max_tokens_per_chunk[chunk_name] = tokens
    
    print()
    print("🎯 TOKEN LIMIT VALIDATION:")
    for chunk_name, max_tokens in max_tokens_per_chunk.items():
        status = "✅" if max_tokens < 50000 else "⚠️" if max_tokens < 70000 else "❌"
        print(f"  {chunk_name}: Max {max_tokens:.0f} tokens {status}")
    
    print()
    print(f"📁 All chunks saved in: {output_dir}")
    
    # Save processing report
    report_data = {
        'processing_summary': {
            'files_processed': len(json_files),
            'successful': successful,
            'failed': failed,
            'total_chunks': total_chunks
        },
        'chunk_statistics': {
            'distribution': {name: {
                'companies': len(counts),
                'avg_metrics': sum(counts) / len(counts),
                'avg_tokens': sum(token_stats[name]) / len(token_stats[name])
            } for name, counts in chunk_stats.items()},
            'max_tokens': max_tokens_per_chunk
        },
        'file_details': results
    }
    
    report_file = "chunking_processing_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"📄 Processing report saved: {report_file}")

if __name__ == "__main__":
    main()

