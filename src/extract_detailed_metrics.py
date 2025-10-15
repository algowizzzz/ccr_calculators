#!/usr/bin/env python3
"""
Extract detailed financial metrics from SEC companyfacts JSON.

Usage:
  python extract_detailed_metrics.py --input companyfacts_0000320193.json --output detailed_metrics.md
  python extract_detailed_metrics.py --input companyfacts_0000320193.json --format json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

def format_currency(value):
    """Format currency values with appropriate units"""
    if value is None:
        return 'N/A'
    if abs(value) >= 1e12:
        return f'${value/1e12:.2f}T'
    elif abs(value) >= 1e9:
        return f'${value/1e9:.2f}B'
    elif abs(value) >= 1e6:
        return f'${value/1e6:.2f}M'
    elif abs(value) >= 1e3:
        return f'${value/1e3:.2f}K'
    else:
        return f'${value:,.0f}'

def get_latest_annual_data(metric_data):
    """Get the most recent annual (10-K) data point"""
    if 'units' not in metric_data:
        return None
    
    for unit_type, entries in metric_data['units'].items():
        annual_entries = [e for e in entries if e.get('form') == '10-K']
        if annual_entries:
            latest = max(annual_entries, key=lambda x: x.get('end', ''))
            return latest
    return None

def get_latest_quarterly_data(metric_data):
    """Get the most recent quarterly (10-Q) data point"""
    if 'units' not in metric_data:
        return None
    
    for unit_type, entries in metric_data['units'].items():
        quarterly_entries = [e for e in entries if e.get('form') == '10-Q']
        if quarterly_entries:
            latest = max(quarterly_entries, key=lambda x: x.get('end', ''))
            return latest
    return None

def extract_comprehensive_metrics(data):
    """Extract comprehensive financial metrics"""
    us_gaap = data['facts'].get('us-gaap', {})
    
    # Comprehensive metric definitions
    metric_categories = {
        'Income Statement': {
            'Revenues': 'Total Revenues',
            'RevenueFromContractWithCustomerExcludingAssessedTax': 'Revenue from Contracts (Excl. Tax)',
            'CostOfGoodsAndServicesSold': 'Cost of Goods Sold',
            'GrossProfit': 'Gross Profit',
            'OperatingIncomeLoss': 'Operating Income',
            'NetIncomeLoss': 'Net Income',
            'EarningsPerShareBasic': 'Earnings Per Share (Basic)',
            'EarningsPerShareDiluted': 'Earnings Per Share (Diluted)'
        },
        'Balance Sheet - Assets': {
            'Assets': 'Total Assets',
            'AssetsCurrent': 'Current Assets',
            'AssetsNoncurrent': 'Non-Current Assets',
            'CashAndCashEquivalentsAtCarryingValue': 'Cash and Cash Equivalents',
            'MarketableSecuritiesCurrent': 'Marketable Securities (Current)',
            'AccountsReceivableNetCurrent': 'Accounts Receivable (Net)',
            'InventoryNet': 'Inventory (Net)',
            'PropertyPlantAndEquipmentNet': 'Property, Plant & Equipment (Net)'
        },
        'Balance Sheet - Liabilities': {
            'Liabilities': 'Total Liabilities',
            'LiabilitiesCurrent': 'Current Liabilities',
            'LiabilitiesNoncurrent': 'Non-Current Liabilities',
            'AccountsPayableCurrent': 'Accounts Payable',
            'AccruedLiabilitiesCurrent': 'Accrued Liabilities',
            'DebtCurrent': 'Short-Term Debt',
            'LongTermDebt': 'Long-Term Debt',
            'LongTermDebtCurrent': 'Current Portion of Long-Term Debt',
            'CommercialPaper': 'Commercial Paper'
        },
        'Balance Sheet - Equity': {
            'StockholdersEquity': 'Stockholders Equity',
            'CommonStocksIncludingAdditionalPaidInCapital': 'Common Stock & Additional Paid-in Capital',
            'RetainedEarningsAccumulatedDeficit': 'Retained Earnings',
            'AccumulatedOtherComprehensiveIncomeLossNetOfTax': 'Accumulated Other Comprehensive Income'
        },
        'Cash Flow': {
            'NetCashProvidedByUsedInOperatingActivities': 'Operating Cash Flow',
            'NetCashProvidedByUsedInInvestingActivities': 'Investing Cash Flow',
            'NetCashProvidedByUsedInFinancingActivities': 'Financing Cash Flow',
            'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect': 'Net Change in Cash'
        }
    }
    
    extracted_metrics = {}
    
    for category, metrics in metric_categories.items():
        extracted_metrics[category] = {}
        for metric_key, display_name in metrics.items():
            if metric_key in us_gaap:
                annual_data = get_latest_annual_data(us_gaap[metric_key])
                quarterly_data = get_latest_quarterly_data(us_gaap[metric_key])
                
                extracted_metrics[category][display_name] = {
                    'annual': annual_data,
                    'quarterly': quarterly_data,
                    'metric_key': metric_key
                }
    
    return extracted_metrics

def calculate_ratios(metrics):
    """Calculate financial ratios"""
    ratios = {}
    
    # Get values for calculations
    def get_annual_value(category, metric_name):
        if category in metrics and metric_name in metrics[category]:
            annual_data = metrics[category][metric_name]['annual']
            return annual_data['val'] if annual_data else None
        return None
    
    # Current Ratio
    current_assets = get_annual_value('Balance Sheet - Assets', 'Current Assets')
    current_liab = get_annual_value('Balance Sheet - Liabilities', 'Current Liabilities')
    if current_assets and current_liab and current_liab != 0:
        ratios['Current Ratio'] = current_assets / current_liab
        ratios['Working Capital'] = current_assets - current_liab
    
    # Profitability Ratios
    revenue = get_annual_value('Income Statement', 'Revenue from Contracts (Excl. Tax)')
    gross_profit = get_annual_value('Income Statement', 'Gross Profit')
    operating_income = get_annual_value('Income Statement', 'Operating Income')
    net_income = get_annual_value('Income Statement', 'Net Income')
    
    if revenue and revenue != 0:
        if gross_profit:
            ratios['Gross Margin %'] = (gross_profit / revenue) * 100
        if operating_income:
            ratios['Operating Margin %'] = (operating_income / revenue) * 100
        if net_income:
            ratios['Net Margin %'] = (net_income / revenue) * 100
    
    # Debt Ratios
    total_assets = get_annual_value('Balance Sheet - Assets', 'Total Assets')
    total_liab = get_annual_value('Balance Sheet - Liabilities', 'Total Liabilities')
    stockholders_equity = get_annual_value('Balance Sheet - Equity', 'Stockholders Equity')
    
    if total_assets and total_liab and total_assets != 0:
        ratios['Debt to Assets %'] = (total_liab / total_assets) * 100
    
    if stockholders_equity and total_liab and stockholders_equity != 0:
        ratios['Debt to Equity'] = total_liab / stockholders_equity
    
    return ratios

def output_markdown(data, metrics, ratios, output_path):
    """Generate markdown output"""
    with open(output_path, 'w') as f:
        f.write(f"# {data['entityName']} - Comprehensive Financial Metrics\n\n")
        f.write(f"**CIK:** {data['cik']}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Metrics by category
        for category, category_metrics in metrics.items():
            f.write(f"## {category}\n\n")
            f.write("| Metric | Latest Annual Value | FY | Latest Quarterly Value | Quarter |\n")
            f.write("|--------|-------------------|----|--------------------|---------|\\n")
            
            for metric_name, data_dict in category_metrics.items():
                annual = data_dict['annual']
                quarterly = data_dict['quarterly']
                
                annual_val = format_currency(annual['val']) if annual else 'N/A'
                annual_fy = annual['fy'] if annual else 'N/A'
                
                quarterly_val = format_currency(quarterly['val']) if quarterly else 'N/A'
                quarterly_fp = quarterly['fp'] if quarterly else 'N/A'
                
                f.write(f"| {metric_name} | {annual_val} | {annual_fy} | {quarterly_val} | {quarterly_fp} |\n")
            
            f.write("\n")
        
        # Financial Ratios
        if ratios:
            f.write("## 📊 Financial Ratios\n\n")
            f.write("| Ratio | Value |\n")
            f.write("|-------|-------|\n")
            
            for ratio_name, ratio_value in ratios.items():
                if 'Margin %' in ratio_name or 'Assets %' in ratio_name:
                    formatted_value = f"{ratio_value:.1f}%"
                elif 'Capital' in ratio_name:
                    formatted_value = format_currency(ratio_value)
                else:
                    formatted_value = f"{ratio_value:.2f}"
                
                f.write(f"| {ratio_name} | {formatted_value} |\n")
            
            f.write("\n")

def output_json(data, metrics, ratios, output_path):
    """Generate JSON output"""
    output_data = {
        'company_info': {
            'cik': data['cik'],
            'entityName': data['entityName'],
            'generated': datetime.now().isoformat()
        },
        'metrics': {},
        'ratios': ratios
    }
    
    # Flatten metrics for JSON
    for category, category_metrics in metrics.items():
        for metric_name, data_dict in category_metrics.items():
            output_data['metrics'][metric_name] = {
                'annual': data_dict['annual'],
                'quarterly': data_dict['quarterly'],
                'category': category,
                'metric_key': data_dict['metric_key']
            }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

def main():
    parser = argparse.ArgumentParser(description='Extract detailed financial metrics from SEC companyfacts JSON')
    parser.add_argument('--input', required=True, help='Input companyfacts JSON file')
    parser.add_argument('--output', help='Output file path (default: detailed_metrics.md)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', 
                       help='Output format (default: markdown)')
    
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
    
    # Extract metrics
    metrics = extract_comprehensive_metrics(data)
    ratios = calculate_ratios(metrics)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base_name = Path(args.input).stem
        extension = '.json' if args.format == 'json' else '.md'
        output_path = f"{base_name}_detailed_metrics{extension}"
    
    # Generate output
    if args.format == 'json':
        output_json(data, metrics, ratios, output_path)
    else:
        output_markdown(data, metrics, ratios, output_path)
    
    print(f"Generated detailed metrics: {output_path}")
    
    # Print summary
    total_metrics = sum(len(category_metrics) for category_metrics in metrics.values())
    print(f"Extracted {total_metrics} metrics across {len(metrics)} categories")
    print(f"Calculated {len(ratios)} financial ratios")

if __name__ == "__main__":
    main()
