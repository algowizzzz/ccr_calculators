#!/usr/bin/env python3
"""
Batch fetch SEC companyfacts data for multiple companies and save in structured format.

This script reads a companies list and fetches SEC data for each company,
saving both raw JSON and extracted key metrics.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# Import our existing modules
try:
    from fetch_companyfacts import make_session, fetch_companyfacts, zero_pad_cik
    from extract_key_metrics import extract_key_metrics
    from analyze_metrics import analyze_all_metrics
except ImportError as e:
    print(f"ERROR: Missing required modules: {e}", file=sys.stderr)
    print("Make sure you're running from the correct directory with all modules available.", file=sys.stderr)
    sys.exit(1)

def parse_companies_file(file_path):
    """Parse the companies file to extract ticker, CIK, and company name"""
    companies = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract table rows using regex
    # Looking for lines like: |  1 | JPMorgan Chase & Co. | JPM | 0000019617 | [url] |
    table_pattern = r'\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d{10})\s*\|[^|]*\|'
    
    matches = re.findall(table_pattern, content)
    
    for match in matches:
        company_name = match[0].strip()
        ticker = match[1].strip()
        cik = match[2].strip()
        
        companies.append({
            'name': company_name,
            'ticker': ticker,
            'cik': cik,
            'cik_padded': zero_pad_cik(cik)
        })
    
    return companies

def create_output_structure(base_dir):
    """Create the output directory structure"""
    base_path = Path(base_dir)
    
    # Create main directories
    dirs_to_create = [
        base_path,
        base_path / "raw_json",
        base_path / "key_metrics", 
        base_path / "catalogs",
        base_path / "summaries"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def fetch_company_data(company_info, session, output_dir):
    """Fetch and process data for a single company"""
    print(f"\n{'='*60}")
    print(f"Processing: {company_info['name']} ({company_info['ticker']})")
    print(f"CIK: {company_info['cik_padded']}")
    print(f"{'='*60}")
    
    results = {
        'company_info': company_info,
        'success': False,
        'files_created': [],
        'error': None,
        'metrics_summary': {}
    }
    
    try:
        # Fetch raw companyfacts data
        print("Fetching SEC companyfacts data...")
        raw_data = fetch_companyfacts(session, company_info['cik_padded'])
        
        # Save raw JSON
        raw_filename = f"companyfacts_{company_info['cik_padded']}.json"
        raw_path = Path(output_dir) / "raw_json" / raw_filename
        
        with open(raw_path, 'w') as f:
            json.dump(raw_data, f, indent=2, default=str)
        results['files_created'].append(str(raw_path))
        print(f"✓ Saved raw data: {raw_path}")
        
        # Extract key metrics
        print("Extracting key financial metrics...")
        key_metrics = extract_key_metrics(raw_data)
        
        # Save key metrics
        metrics_filename = f"{company_info['ticker'].lower()}_key_metrics.json"
        metrics_path = Path(output_dir) / "key_metrics" / metrics_filename
        
        with open(metrics_path, 'w') as f:
            json.dump(key_metrics, f, indent=2, default=str)
        results['files_created'].append(str(metrics_path))
        print(f"✓ Saved key metrics: {metrics_path}")
        
        # Generate full metrics catalog
        print("Generating comprehensive metrics catalog...")
        catalog = analyze_all_metrics(raw_data)
        
        # Save catalog
        catalog_filename = f"{company_info['ticker'].lower()}_catalog.json"
        catalog_path = Path(output_dir) / "catalogs" / catalog_filename
        
        with open(catalog_path, 'w') as f:
            json.dump(catalog, f, indent=2, default=str)
        results['files_created'].append(str(catalog_path))
        print(f"✓ Saved catalog: {catalog_path}")
        
        # Create summary
        summary = {
            'company_name': raw_data.get('entityName'),
            'ticker': company_info['ticker'],
            'cik': company_info['cik_padded'],
            'processing_date': datetime.now().isoformat(),
            'total_metrics': catalog['summary']['total_metrics'],
            'taxonomies': list(catalog['taxonomies'].keys()),
            'key_metrics_found': sum(1 for m in key_metrics['metrics'].values() if m['sec_key'] is not None),
            'key_metrics_total': len(key_metrics['metrics']),
            'categories': dict(catalog['summary']['categories']),
            'date_range': {
                'earliest': None,
                'latest': None
            }
        }
        
        # Find date range
        all_dates = []
        for taxonomy_data in catalog['taxonomies'].values():
            for metric_info in taxonomy_data['metrics'].values():
                if metric_info['date_range']['earliest']:
                    all_dates.append(metric_info['date_range']['earliest'])
                if metric_info['date_range']['latest']:
                    all_dates.append(metric_info['date_range']['latest'])
        
        if all_dates:
            summary['date_range']['earliest'] = min(all_dates)
            summary['date_range']['latest'] = max(all_dates)
        
        # Save summary
        summary_filename = f"{company_info['ticker'].lower()}_summary.json"
        summary_path = Path(output_dir) / "summaries" / summary_filename
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        results['files_created'].append(str(summary_path))
        print(f"✓ Saved summary: {summary_path}")
        
        results['success'] = True
        results['metrics_summary'] = {
            'total_metrics': catalog['summary']['total_metrics'],
            'taxonomies': len(catalog['taxonomies']),
            'key_metrics_found': summary['key_metrics_found'],
            'date_range': summary['date_range']
        }
        
        print(f"✓ Successfully processed {company_info['name']}")
        print(f"  - Total metrics: {results['metrics_summary']['total_metrics']}")
        print(f"  - Key metrics found: {results['metrics_summary']['key_metrics_found']}/29")
        print(f"  - Files created: {len(results['files_created'])}")
        
    except Exception as e:
        results['error'] = str(e)
        print(f"✗ Error processing {company_info['name']}: {e}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Batch fetch SEC data for multiple companies')
    parser.add_argument('--companies-file', default='sec_metrics_data/companies', 
                       help='File containing company list (default: sec_metrics_data/companies)')
    parser.add_argument('--output-dir', default='sec_metrics_data',
                       help='Output directory (default: sec_metrics_data)')
    parser.add_argument('--user-agent', default='Financial Analysis Tool analyst@example.com',
                       help='User agent for SEC requests')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process (for testing)')
    parser.add_argument('--start-from', type=int, default=0, help='Start from company index (0-based)')
    
    args = parser.parse_args()
    
    # Parse companies file
    try:
        companies = parse_companies_file(args.companies_file)
        print(f"Found {len(companies)} companies in {args.companies_file}")
    except Exception as e:
        print(f"ERROR: Failed to parse companies file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Apply start-from and limit
    if args.start_from > 0:
        companies = companies[args.start_from:]
        print(f"Starting from company index {args.start_from}")
    
    if args.limit:
        companies = companies[:args.limit]
        print(f"Limited to {args.limit} companies")
    
    # Create output structure
    create_output_structure(args.output_dir)
    
    # Create session
    session = make_session(args.user_agent)
    
    # Process companies
    results = []
    successful = 0
    failed = 0
    
    print(f"\nStarting batch processing of {len(companies)} companies...")
    print(f"Output directory: {args.output_dir}")
    print(f"Delay between requests: {args.delay}s")
    
    start_time = time.time()
    
    for i, company in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}] Processing {company['ticker']}...")
        
        result = fetch_company_data(company, session, args.output_dir)
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
        
        # Delay between requests to be respectful
        if i < len(companies):  # Don't delay after the last company
            time.sleep(args.delay)
    
    # Generate final report
    end_time = time.time()
    duration = end_time - start_time
    
    report = {
        'processing_summary': {
            'total_companies': len(companies),
            'successful': successful,
            'failed': failed,
            'success_rate': f"{(successful/len(companies)*100):.1f}%",
            'duration_seconds': duration,
            'duration_formatted': f"{duration/60:.1f} minutes"
        },
        'companies': results,
        'generated': datetime.now().isoformat()
    }
    
    # Save report
    report_path = Path(args.output_dir) / "batch_processing_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print(f"\n{'='*80}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Total companies: {len(companies)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(companies)*100):.1f}%")
    print(f"Duration: {duration/60:.1f} minutes")
    print(f"Report saved: {report_path}")
    
    if failed > 0:
        print(f"\nFailed companies:")
        for result in results:
            if not result['success']:
                print(f"  - {result['company_info']['ticker']} ({result['company_info']['name']}): {result['error']}")

if __name__ == "__main__":
    main()

