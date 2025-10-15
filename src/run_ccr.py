#!/usr/bin/env python3
"""
Unified CCR Calculator Runner

Usage:
    python3 src/run_ccr.py max T101
    python3 src/run_ccr.py percentile T202  
    python3 src/run_ccr.py netting T101
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).resolve().parent))
from ccr_calculators import CCRCalculators

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 src/run_ccr.py <calculator> <trade_id>")
        print("\nAvailable calculators:")
        print("  max        - PFE Max Calculator")
        print("  percentile - FV Percentile Calculator")
        print("  netting    - Netting Set Calculator (SIM-based)")
        print("  quick      - QUICK PFE Calculator")
        print("  sim        - SIM PFE Calculator")
        print("  combined   - Combined PFE Calculator (SIM + QUICK)")
        print("  limits     - Limit Matching Calculator")
        print("  breaches   - Breach Detection Calculator")
        print("\nExamples:")
        print("  python3 src/run_ccr.py max T101")
        print("  python3 src/run_ccr.py percentile T202")
        print("  python3 src/run_ccr.py netting T101")
        sys.exit(1)

    calculator_type = sys.argv[1].lower()
    trade_id = sys.argv[2]

    try:
        if calculator_type == "max":
            result = CCRCalculators.max_trade_value(trade_id)
        elif calculator_type == "percentile":
            result = CCRCalculators.fv_percentile(trade_id)
        elif calculator_type == "netting":
            result = CCRCalculators.netting_from_trade(trade_id)
        elif calculator_type == "quick":
            result = CCRCalculators.quick_pfe(trade_id)
        elif calculator_type == "sim":
            result = CCRCalculators.sim_pfe(trade_id)
        elif calculator_type == "combined":
            result = CCRCalculators.combined_pfe(trade_id)
        elif calculator_type == "limits":
            result = CCRCalculators.match_limits(trade_id)
        elif calculator_type == "breaches":
            result = CCRCalculators.check_breaches(trade_id)
        else:
            print(f"Error: Unknown calculator type '{calculator_type}'")
            print("Available: max, percentile, netting, quick, sim, combined, limits, breaches")
            sys.exit(1)
            
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
