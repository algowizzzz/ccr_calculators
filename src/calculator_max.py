
from datetime import datetime, timezone
from typing import Dict, Any
from cache_store import load_cache, save_cache, save_output  # absolute import (sys.path is set by caller)

def max_trade_value(trade_id: str) -> Dict[str, Any]:
    """
    Stateless calculator:
      - arg: trade_id only
      - reads vector from cache["trade.vectors"][trade_id]
      - returns {"trade.max.value": <number|null>, "trade.max.calc_ts": <iso>}
      - persists result to outputs/ and merges back into cache
    """
    cache: Dict[str, Any] = load_cache()
    vectors = cache.get("trade.vectors", {})
    vector = vectors.get(trade_id, [])

    ts = datetime.now(timezone.utc).isoformat()
    result: Dict[str, Any] = {
        "trade.max.value": (max(vector) if vector else None),
        "trade.max.calc_ts": ts,
    }

    # merge into cache (write-once, overwrite prior values)
    cache.update(result)
    save_cache(cache)

    # also save a per-trade output
    save_output(trade_id, result)

    return result
