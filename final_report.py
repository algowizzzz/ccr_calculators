#!/usr/bin/env python3
"""
Generate final comprehensive report for SEC metrics data collection.
"""

import json
from pathlib import Path
from datetime import datetime

def generate_final_report():
    base_dir = Path("sec_metrics_data")
    
    # Get all processed companies
    processed_companies = []
    if (base_dir / "key_metrics").exists():
        for file in (base_dir / "key_metrics").glob("*.json"):
            ticker = file.stem.replace("_key_metrics", "").upper()
            
            # Load summary for additional info
            summary_file = base_dir / "summaries" / f"{ticker.lower()}_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                processed_companies.append({
                    'ticker': ticker,
                    'company_name': summary.get('company_name', 'N/A'),
                    'cik': summary.get('cik', 'N/A'),
                    'total_metrics': summary.get('total_metrics', 0),
                    'key_metrics_found': summary.get('key_metrics_found', 0),
                    'taxonomies': summary.get('taxonomies', []),
                    'date_range': summary.get('date_range', {})
                })
    
    # Sort by ticker
    processed_companies.sort(key=lambda x: x['ticker'])
    
    # Identify missing companies from original list
    original_companies = [
        'JPM', 'BAC', 'WFC', 'C', 'MS', 'GS', 'SCHW', 'PNC', 'USB', 'BK',
        'TFC', 'COF', 'STT', 'NTRS', 'FITB', 'HBAN', 'RF', 'CFG', 'KEY', 'MTB',
        'FCNCA', 'CMA', 'ZION', 'ALLY', 'RY', 'TD', 'BNS', 'BMO', 'CM', 'NA'
    ]
    
    processed_tickers = [c['ticker'] for c in processed_companies]
    missing_companies = [ticker for ticker in original_companies if ticker not in processed_tickers]
    
    # Calculate statistics
    us_banks = [c for c in processed_companies if c['ticker'] not in ['RY', 'TD', 'BNS', 'BMO', 'CM']]
    canadian_banks = [c for c in processed_companies if c['ticker'] in ['RY', 'TD', 'BNS', 'BMO', 'CM']]
    
    # Create final report
    report = {
        'report_metadata': {
            'generated': datetime.now().isoformat(),
            'title': 'SEC Financial Metrics Data Collection - Final Report',
            'version': '1.0'
        },
        'executive_summary': {
            'total_companies_targeted': 30,
            'companies_successfully_processed': len(processed_companies),
            'success_rate': f"{(len(processed_companies)/30*100):.1f}%",
            'companies_missing_data': len(missing_companies),
            'total_data_size_mb': f"{sum(f.stat().st_size for f in Path('sec_metrics_data').rglob('*.json'))/(1024*1024):.1f}",
            'us_banks_processed': len(us_banks),
            'canadian_banks_processed': len(canadian_banks)
        },
        'data_quality_analysis': {
            'avg_metrics_per_company': sum(c['total_metrics'] for c in processed_companies) / len(processed_companies) if processed_companies else 0,
            'avg_key_metrics_found': sum(c['key_metrics_found'] for c in processed_companies) / len(processed_companies) if processed_companies else 0,
            'key_metrics_success_rate': f"{(sum(c['key_metrics_found'] for c in processed_companies) / (len(processed_companies) * 29) * 100):.1f}%" if processed_companies else "0%",
            'taxonomies_found': list(set(tax for c in processed_companies for tax in c['taxonomies'])),
            'date_coverage': {
                'earliest': min((c['date_range'].get('earliest') for c in processed_companies if c['date_range'].get('earliest')), default=None),
                'latest': max((c['date_range'].get('latest') for c in processed_companies if c['date_range'].get('latest')), default=None)
            }
        },
        'processed_companies': processed_companies,
        'missing_companies': [
            {'ticker': ticker, 'reason': 'No SEC companyfacts data available' if ticker in ['ALLY', 'NA'] else 'Processing error'}
            for ticker in missing_companies
        ],
        'file_structure': {
            'raw_json': len(list((base_dir / "raw_json").glob("*.json"))) if (base_dir / "raw_json").exists() else 0,
            'key_metrics': len(list((base_dir / "key_metrics").glob("*.json"))) if (base_dir / "key_metrics").exists() else 0,
            'catalogs': len(list((base_dir / "catalogs").glob("*.json"))) if (base_dir / "catalogs").exists() else 0,
            'summaries': len(list((base_dir / "summaries").glob("*.json"))) if (base_dir / "summaries").exists() else 0
        }
    }
    
    return report

def print_report(report):
    print("=" * 100)
    print("🏦 SEC FINANCIAL METRICS DATA COLLECTION - FINAL REPORT")
    print("=" * 100)
    print(f"Generated: {report['report_metadata']['generated']}")
    print()
    
    exec_summary = report['executive_summary']
    print("📊 EXECUTIVE SUMMARY")
    print("-" * 50)
    print(f"Target Companies: {exec_summary['total_companies_targeted']}")
    print(f"Successfully Processed: {exec_summary['companies_successfully_processed']} ({exec_summary['success_rate']})")
    print(f"Missing Data: {exec_summary['companies_missing_data']} companies")
    print(f"Total Data Size: {exec_summary['total_data_size_mb']} MB")
    print(f"US Banks: {exec_summary['us_banks_processed']}")
    print(f"Canadian Banks: {exec_summary['canadian_banks_processed']}")
    print()
    
    quality = report['data_quality_analysis']
    print("📈 DATA QUALITY ANALYSIS")
    print("-" * 50)
    print(f"Average Metrics per Company: {quality['avg_metrics_per_company']:.0f}")
    print(f"Average Key Metrics Found: {quality['avg_key_metrics_found']:.1f}/29")
    print(f"Key Metrics Success Rate: {quality['key_metrics_success_rate']}")
    print(f"Taxonomies Found: {', '.join(quality['taxonomies_found'])}")
    print(f"Date Coverage: {quality['date_coverage']['earliest']} to {quality['date_coverage']['latest']}")
    print()
    
    print("🏛️ PROCESSED COMPANIES")
    print("-" * 50)
    for company in report['processed_companies']:
        taxonomies_str = ', '.join(company['taxonomies'])
        print(f"{company['ticker']:5} | {company['company_name'][:40]:40} | {company['total_metrics']:4d} metrics | {company['key_metrics_found']:2d}/29 key | {taxonomies_str}")
    
    if report['missing_companies']:
        print()
        print("❌ MISSING COMPANIES")
        print("-" * 50)
        for missing in report['missing_companies']:
            print(f"{missing['ticker']:5} | {missing['reason']}")
    
    print()
    print("📁 FILES CREATED")
    print("-" * 50)
    files = report['file_structure']
    print(f"Raw JSON files: {files['raw_json']}")
    print(f"Key Metrics files: {files['key_metrics']}")
    print(f"Catalog files: {files['catalogs']}")
    print(f"Summary files: {files['summaries']}")
    print(f"Total files: {sum(files.values())}")

if __name__ == "__main__":
    report = generate_final_report()
    print_report(report)
    
    # Save report
    with open('sec_metrics_data/final_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved: sec_metrics_data/final_report.json")

