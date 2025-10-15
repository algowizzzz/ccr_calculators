#!/usr/bin/env python3
"""
Gap Analysis: Universal Metrics vs Complete Metrics
Business perspective analysis comparing coverage and missing metrics
"""

import json
from pathlib import Path
from collections import defaultdict

def load_universal_metrics():
    """Load universal metrics master file"""
    universal_file = Path("sec_metrics_data/universal_metrics_min20.json")
    with open(universal_file, 'r') as f:
        return json.load(f)

def load_complete_metrics_sample():
    """Load a sample complete metrics file for comparison"""
    complete_dir = Path("sec_metrics_data/complete_metrics")
    # Use Bank of America as representative sample
    bac_file = complete_dir / "Bank_of_America_Corporation_all_metrics.json"
    with open(bac_file, 'r') as f:
        return json.load(f)

def categorize_metrics(metrics_dict):
    """Categorize metrics by business function"""
    categories = {
        'Capital & Risk': [],
        'Assets & Liabilities': [],
        'Revenue & Income': [],
        'Regulatory & Compliance': [],
        'Operations & Efficiency': [],
        'Market & Trading': [],
        'Credit & Loans': [],
        'Other': []
    }
    
    for metric_name in metrics_dict.keys():
        name_lower = metric_name.lower()
        
        if any(term in name_lower for term in ['capital', 'tier', 'ratio', 'risk', 'leverage', 'adequacy']):
            categories['Capital & Risk'].append(metric_name)
        elif any(term in name_lower for term in ['asset', 'liabilit', 'deposit', 'cash', 'securities', 'investment']):
            categories['Assets & Liabilities'].append(metric_name)
        elif any(term in name_lower for term in ['revenue', 'income', 'interest', 'fee', 'earnings', 'profit']):
            categories['Revenue & Income'].append(metric_name)
        elif any(term in name_lower for term in ['regulatory', 'compliance', 'allowance', 'provision', 'reserve']):
            categories['Regulatory & Compliance'].append(metric_name)
        elif any(term in name_lower for term in ['expense', 'cost', 'efficiency', 'employee', 'operating']):
            categories['Operations & Efficiency'].append(metric_name)
        elif any(term in name_lower for term in ['trading', 'market', 'derivative', 'fair', 'unrealized']):
            categories['Market & Trading'].append(metric_name)
        elif any(term in name_lower for term in ['loan', 'credit', 'mortgage', 'financing', 'receivable']):
            categories['Credit & Loans'].append(metric_name)
        else:
            categories['Other'].append(metric_name)
    
    return categories

def main():
    print("🔍 GAP ANALYSIS: Universal vs Complete Metrics")
    print("=" * 80)
    
    # Load data
    print("Loading data files...")
    universal_data = load_universal_metrics()
    complete_data = load_complete_metrics_sample()
    
    universal_metrics = universal_data['universal_metrics_catalog']
    complete_metrics = complete_data['all_metrics']
    
    # Basic statistics
    universal_count = len(universal_metrics)
    complete_count = len(complete_metrics)
    
    print(f"📊 Universal Metrics: {universal_count:,} metrics")
    print(f"📊 Complete Metrics: {complete_count:,} metrics (Bank of America sample)")
    print(f"📊 Coverage Gap: {complete_count - universal_count:,} metrics ({((complete_count - universal_count)/complete_count)*100:.1f}%)")
    print()
    
    # Find missing metrics (in complete but not in universal)
    universal_set = set(universal_metrics.keys())
    complete_set = set(complete_metrics.keys())
    
    missing_in_universal = complete_set - universal_set
    missing_count = len(missing_in_universal)
    
    print("🎯 BUSINESS IMPACT ANALYSIS")
    print("=" * 80)
    
    # Categorize all metrics
    universal_categories = categorize_metrics(universal_metrics)
    complete_categories = categorize_metrics(complete_metrics)
    missing_categories = categorize_metrics({k: None for k in missing_in_universal})
    
    print("📈 COVERAGE BY BUSINESS AREA:")
    print()
    for category, metrics in complete_categories.items():
        if not metrics:
            continue
            
        total_in_category = len(metrics)
        universal_in_category = len(universal_categories.get(category, []))
        missing_in_category = len(missing_categories.get(category, []))
        coverage_pct = (universal_in_category / total_in_category) * 100 if total_in_category > 0 else 0
        
        print(f"  {category:25} | Total: {total_in_category:3d} | Universal: {universal_in_category:3d} | Missing: {missing_in_category:3d} | Coverage: {coverage_pct:5.1f}%")
    
    print()
    print("🚨 CRITICAL BUSINESS GAPS:")
    print("=" * 80)
    
    # Analyze critical missing metrics by category
    critical_gaps = {
        'Capital & Risk': [],
        'Revenue & Income': [],
        'Credit & Loans': [],
        'Regulatory & Compliance': []
    }
    
    for metric in missing_in_universal:
        metric_lower = metric.lower()
        
        # Capital & Risk gaps
        if any(term in metric_lower for term in ['tier1', 'tier2', 'riskweighted', 'leverageratio', 'capitalratio']):
            critical_gaps['Capital & Risk'].append(metric)
        
        # Revenue gaps  
        elif any(term in metric_lower for term in ['netinterestincome', 'noninterestincome', 'tradingrevenue']):
            critical_gaps['Revenue & Income'].append(metric)
        
        # Credit gaps
        elif any(term in metric_lower for term in ['creditloss', 'nonperforming', 'chargeoff', 'loanlosses']):
            critical_gaps['Credit & Loans'].append(metric)
        
        # Regulatory gaps
        elif any(term in metric_lower for term in ['allowance', 'provision', 'reserve', 'impairment']):
            critical_gaps['Regulatory & Compliance'].append(metric)
    
    for category, gaps in critical_gaps.items():
        if gaps:
            print(f"\n🔴 {category}:")
            for i, gap in enumerate(gaps[:3], 1):  # Show top 3
                label = complete_metrics.get(gap, {}).get('label', 'No label')
                print(f"  {i}. {gap}")
                print(f"     → {label}")
            if len(gaps) > 3:
                print(f"     ... and {len(gaps) - 3} more")
    
    print()
    print("💼 BUSINESS IMPLICATIONS:")
    print("=" * 80)
    
    # Business impact assessment
    implications = [
        {
            'area': 'Risk Management',
            'impact': 'HIGH',
            'issue': f'{len(missing_categories["Capital & Risk"])} missing capital/risk metrics',
            'consequence': 'Incomplete risk assessment, regulatory compliance gaps'
        },
        {
            'area': 'Credit Analysis', 
            'impact': 'HIGH',
            'issue': f'{len(missing_categories["Credit & Loans"])} missing credit metrics',
            'consequence': 'Limited loan portfolio analysis, credit risk blind spots'
        },
        {
            'area': 'Financial Performance',
            'impact': 'MEDIUM',
            'issue': f'{len(missing_categories["Revenue & Income"])} missing revenue metrics',
            'consequence': 'Reduced granularity in profitability analysis'
        },
        {
            'area': 'Operational Efficiency',
            'impact': 'MEDIUM', 
            'issue': f'{len(missing_categories["Operations & Efficiency"])} missing operational metrics',
            'consequence': 'Limited cost analysis and efficiency benchmarking'
        }
    ]
    
    for imp in implications:
        impact_color = "🔴" if imp['impact'] == 'HIGH' else "🟡"
        print(f"{impact_color} {imp['area']} ({imp['impact']} IMPACT):")
        print(f"   Issue: {imp['issue']}")
        print(f"   Impact: {imp['consequence']}")
        print()
    
    print("📋 RECOMMENDATIONS:")
    print("=" * 80)
    
    recommendations = [
        "1. 🎯 USE CASES:",
        "   • Universal Metrics: Cross-bank comparisons, standardized reporting, CCR calculations",
        "   • Complete Metrics: Deep-dive analysis, regulatory compliance, detailed risk assessment",
        "",
        "2. 🔄 HYBRID APPROACH:",
        "   • Start with Universal Metrics for baseline analysis",
        "   • Supplement with Complete Metrics for specific business areas",
        "   • Focus on high-impact missing metrics first",
        "",
        "3. 🎪 PRIORITIZATION:",
        f"   • Address {len(critical_gaps['Capital & Risk'])} critical capital/risk gaps immediately",
        f"   • Enhance credit analysis with {len(critical_gaps['Credit & Loans'])} missing credit metrics", 
        "   • Consider company-specific metrics for unique business models",
        "",
        "4. 📊 DATA STRATEGY:",
        "   • Universal: ~1.3K tokens per bank (efficient for LLM processing)",
        "   • Complete: ~186K tokens average (comprehensive but resource-intensive)",
        f"   • Gap represents {missing_count:,} metrics ({((missing_count/complete_count)*100):.1f}% of total information)"
    ]
    
    for rec in recommendations:
        print(rec)
    
    print()
    print("=" * 80)
    print(f"💡 SUMMARY: Universal metrics provide {((universal_count/complete_count)*100):.1f}% coverage")
    print(f"   Efficient for standardized analysis but gaps exist in specialized areas")
    print(f"   Complete metrics essential for comprehensive risk and regulatory analysis")

if __name__ == "__main__":
    main()
