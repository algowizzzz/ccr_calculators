#!/usr/bin/env python3
"""
Extract key financial metrics from SEC companyfacts JSON in a structured format.

This script focuses on the most commonly used financial metrics and organizes
them in a clean, structured JSON format suitable for financial analysis.

Usage:
  python extract_key_metrics.py --input companyfacts_0000320193.json --output key_metrics.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

def get_latest_annual_value(metric_data, unit='USD'):
    """Get the most recent annual (10-K) value for a metric"""
    if not metric_data or 'units' not in metric_data:
        return None
    
    unit_data = metric_data['units'].get(unit, [])
    if not unit_data:
        # Try other common units if USD not available
        for alt_unit in ['shares', 'pure', 'USD/shares']:
            unit_data = metric_data['units'].get(alt_unit, [])
            if unit_data:
                break
    
    # Filter for annual reports (10-K forms)
    annual_data = [item for item in unit_data if item.get('form') == '10-K']
    
    if not annual_data:
        return None
    
    # Get the most recent
    latest = max(annual_data, key=lambda x: x.get('end', ''))
    return {
        'value': latest.get('val'),
        'date': latest.get('end'),
        'fiscal_year': latest.get('fy'),
        'form': latest.get('form'),
        'filed': latest.get('filed')
    }

def get_latest_quarterly_value(metric_data, unit='USD'):
    """Get the most recent quarterly value for a metric"""
    if not metric_data or 'units' not in metric_data:
        return None
    
    unit_data = metric_data['units'].get(unit, [])
    if not unit_data:
        # Try other common units
        for alt_unit in ['shares', 'pure', 'USD/shares']:
            unit_data = metric_data['units'].get(alt_unit, [])
            if unit_data:
                break
    
    # Filter for quarterly reports (10-Q forms)
    quarterly_data = [item for item in unit_data if item.get('form') == '10-Q']
    
    if not quarterly_data:
        return None
    
    # Get the most recent
    latest = max(quarterly_data, key=lambda x: x.get('end', ''))
    return {
        'value': latest.get('val'),
        'date': latest.get('end'),
        'fiscal_year': latest.get('fy'),
        'fiscal_period': latest.get('fp'),
        'form': latest.get('form'),
        'filed': latest.get('filed')
    }

def extract_key_metrics(companyfacts_data):
    """Extract key financial metrics in a structured format"""
    
    # Get taxonomy data
    us_gaap = companyfacts_data['facts'].get('us-gaap', {})
    dei = companyfacts_data['facts'].get('dei', {})
    
    # Define key metrics to extract
    key_metrics = {
        # Revenue & Income Statement
        'revenue': {
            'keys': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
            'category': 'Income Statement',
            'description': 'Total Revenue'
        },
        'cost_of_revenue': {
            'keys': ['CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfSales'],
            'category': 'Income Statement',
            'description': 'Cost of Goods/Services Sold'
        },
        'gross_profit': {
            'keys': ['GrossProfit'],
            'category': 'Income Statement',
            'description': 'Gross Profit'
        },
        'operating_income': {
            'keys': ['OperatingIncomeLoss'],
            'category': 'Income Statement',
            'description': 'Operating Income'
        },
        'net_income': {
            'keys': ['NetIncomeLoss'],
            'category': 'Income Statement',
            'description': 'Net Income'
        },
        'earnings_per_share_basic': {
            'keys': ['EarningsPerShareBasic'],
            'category': 'Income Statement',
            'description': 'Earnings Per Share (Basic)'
        },
        'earnings_per_share_diluted': {
            'keys': ['EarningsPerShareDiluted'],
            'category': 'Income Statement',
            'description': 'Earnings Per Share (Diluted)'
        },
        
        # Balance Sheet - Assets
        'total_assets': {
            'keys': ['Assets'],
            'category': 'Balance Sheet',
            'description': 'Total Assets'
        },
        'current_assets': {
            'keys': ['AssetsCurrent'],
            'category': 'Balance Sheet',
            'description': 'Current Assets'
        },
        'cash_and_equivalents': {
            'keys': ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'],
            'category': 'Balance Sheet',
            'description': 'Cash and Cash Equivalents'
        },
        'marketable_securities': {
            'keys': ['MarketableSecuritiesCurrent', 'AvailableForSaleSecuritiesDebtSecurities'],
            'category': 'Balance Sheet',
            'description': 'Marketable Securities'
        },
        'accounts_receivable': {
            'keys': ['AccountsReceivableNetCurrent'],
            'category': 'Balance Sheet',
            'description': 'Accounts Receivable'
        },
        'inventory': {
            'keys': ['InventoryNet'],
            'category': 'Balance Sheet',
            'description': 'Inventory'
        },
        'property_plant_equipment': {
            'keys': ['PropertyPlantAndEquipmentNet'],
            'category': 'Balance Sheet',
            'description': 'Property, Plant & Equipment (Net)'
        },
        
        # Balance Sheet - Liabilities
        'total_liabilities': {
            'keys': ['Liabilities'],
            'category': 'Balance Sheet',
            'description': 'Total Liabilities'
        },
        'current_liabilities': {
            'keys': ['LiabilitiesCurrent'],
            'category': 'Balance Sheet',
            'description': 'Current Liabilities'
        },
        'accounts_payable': {
            'keys': ['AccountsPayableCurrent'],
            'category': 'Balance Sheet',
            'description': 'Accounts Payable'
        },
        'short_term_debt': {
            'keys': ['DebtCurrent', 'ShortTermBorrowings'],
            'category': 'Balance Sheet',
            'description': 'Short-Term Debt'
        },
        'long_term_debt': {
            'keys': ['LongTermDebt'],
            'category': 'Balance Sheet',
            'description': 'Long-Term Debt'
        },
        'commercial_paper': {
            'keys': ['CommercialPaper'],
            'category': 'Balance Sheet',
            'description': 'Commercial Paper'
        },
        
        # Balance Sheet - Equity
        'stockholders_equity': {
            'keys': ['StockholdersEquity'],
            'category': 'Balance Sheet',
            'description': 'Stockholders Equity'
        },
        'retained_earnings': {
            'keys': ['RetainedEarningsAccumulatedDeficit'],
            'category': 'Balance Sheet',
            'description': 'Retained Earnings'
        },
        
        # Share Information
        'shares_outstanding': {
            'keys': ['CommonStockSharesOutstanding', 'EntityCommonStockSharesOutstanding'],
            'category': 'Share Information',
            'description': 'Common Stock Shares Outstanding'
        },
        'weighted_average_shares_basic': {
            'keys': ['WeightedAverageNumberOfSharesOutstandingBasic'],
            'category': 'Share Information',
            'description': 'Weighted Average Shares Outstanding (Basic)'
        },
        'weighted_average_shares_diluted': {
            'keys': ['WeightedAverageNumberOfDilutedSharesOutstanding'],
            'category': 'Share Information',
            'description': 'Weighted Average Shares Outstanding (Diluted)'
        },
        
        # Cash Flow Statement
        'operating_cash_flow': {
            'keys': ['NetCashProvidedByUsedInOperatingActivities'],
            'category': 'Cash Flow',
            'description': 'Net Cash from Operating Activities'
        },
        'investing_cash_flow': {
            'keys': ['NetCashProvidedByUsedInInvestingActivities'],
            'category': 'Cash Flow',
            'description': 'Net Cash from Investing Activities'
        },
        'financing_cash_flow': {
            'keys': ['NetCashProvidedByUsedInFinancingActivities'],
            'category': 'Cash Flow',
            'description': 'Net Cash from Financing Activities'
        },
        'free_cash_flow': {
            'keys': ['FreeCashFlow'],
            'category': 'Cash Flow',
            'description': 'Free Cash Flow'
        }
    }
    
    # Extract the metrics
    results = {
        'company_info': {
            'cik': companyfacts_data.get('cik'),
            'entity_name': companyfacts_data.get('entityName'),
            'extraction_date': datetime.now().isoformat()
        },
        'metrics': {}
    }
    
    for metric_id, metric_config in key_metrics.items():
        # Try to find the metric using the provided keys
        metric_data = None
        found_key = None
        
        for key in metric_config['keys']:
            if key in us_gaap:
                metric_data = us_gaap[key]
                found_key = key
                break
            elif key in dei:
                metric_data = dei[key]
                found_key = key
                break
        
        if metric_data:
            # Determine appropriate unit
            units = list(metric_data.get('units', {}).keys())
            primary_unit = 'USD' if 'USD' in units else (units[0] if units else None)
            
            annual_data = get_latest_annual_value(metric_data, primary_unit)
            quarterly_data = get_latest_quarterly_value(metric_data, primary_unit)
            
            results['metrics'][metric_id] = {
                'description': metric_config['description'],
                'category': metric_config['category'],
                'sec_key': found_key,
                'unit': primary_unit,
                'available_units': units,
                'annual': annual_data,
                'quarterly': quarterly_data,
                'label': metric_data.get('label'),
                'sec_description': metric_data.get('description')
            }
        else:
            # Metric not found
            results['metrics'][metric_id] = {
                'description': metric_config['description'],
                'category': metric_config['category'],
                'sec_key': None,
                'unit': None,
                'available_units': [],
                'annual': None,
                'quarterly': None,
                'label': None,
                'sec_description': 'Metric not found in SEC data'
            }
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Extract key financial metrics from SEC companyfacts JSON')
    parser.add_argument('--input', required=True, help='Input companyfacts JSON file')
    parser.add_argument('--output', help='Output JSON file (default: key_metrics.json)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
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
    
    print("Extracting key financial metrics...")
    results = extract_key_metrics(data)
    
    # Determine output path
    output_path = args.output if args.output else 'key_metrics.json'
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2 if args.pretty else None, default=str)
    
    print(f"Generated key metrics: {output_path}")
    
    # Print summary
    found_metrics = sum(1 for metric in results['metrics'].values() if metric['sec_key'] is not None)
    total_metrics = len(results['metrics'])
    
    print(f"\nSUMMARY:")
    print(f"- Total key metrics defined: {total_metrics}")
    print(f"- Metrics found in SEC data: {found_metrics}")
    print(f"- Metrics not found: {total_metrics - found_metrics}")
    
    # Show metrics by category
    categories = {}
    for metric_id, metric_data in results['metrics'].items():
        category = metric_data['category']
        if category not in categories:
            categories[category] = {'found': 0, 'total': 0}
        categories[category]['total'] += 1
        if metric_data['sec_key']:
            categories[category]['found'] += 1
    
    print(f"\nMETRICS BY CATEGORY:")
    for category, stats in categories.items():
        print(f"- {category}: {stats['found']}/{stats['total']} found")

if __name__ == "__main__":
    main()

