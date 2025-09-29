
import sys, json
from pathlib import Path

# allow "python src/run_max.py T101"
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/run_max.py <TRADE_ID>")
        sys.exit(1)

    trade_id = sys.argv[1]

    # local import (package-less)
    sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
    from calculator_max import max_trade_value

    result = max_trade_value(trade_id)
    print(json.dumps(result, indent=2))
