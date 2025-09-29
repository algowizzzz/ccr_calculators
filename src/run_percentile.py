import sys, json
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/run_percentile.py <TRADE_ID>")
        sys.exit(1)

    trade_id = sys.argv[1]
    sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
    from calculator_percentile import fv_percentile

    result = fv_percentile(trade_id)
    print(json.dumps(result, indent=2))
