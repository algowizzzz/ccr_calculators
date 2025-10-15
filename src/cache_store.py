
import json
from pathlib import Path
from typing import Dict, Any

BASE = Path(__file__).resolve().parents[1]
CACHE_PATH = BASE / "cache" / "cache.json"
OUTPUTS_DIR = BASE / "outputs"

def load_cache() -> Dict[str, Any]:
    """Load cache data from multiple data files"""
    data_dir = BASE / "data"
    cache = {}
    
    # Load from individual data files
    files_to_load = [
        ("trades.json", "trades"),
        ("sim_matrices.json", "sim_matrices"), 
        ("quick_vectors.json", "quick_vectors"),
        ("limits.json", "limits"),
        ("netting_sets.json", "netting_sets")
    ]
    
    for filename, key in files_to_load:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding="utf-8") as f:
                    cache[key] = json.load(f)
            except json.JSONDecodeError:
                continue
    
    # Load legacy cache.json if it exists
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                legacy_cache = json.load(f)
                cache.update(legacy_cache)
        except json.JSONDecodeError:
            pass
    
    return cache

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
