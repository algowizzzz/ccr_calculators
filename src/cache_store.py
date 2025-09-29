
import json
from pathlib import Path
from typing import Dict, Any

BASE = Path(__file__).resolve().parents[1]
CACHE_PATH = BASE / "cache" / "cache.json"
OUTPUTS_DIR = BASE / "outputs"

def load_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache: Dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def save_output(trade_id: str, result: Dict[str, Any]) -> str:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / f"result_{trade_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return str(out_path)
