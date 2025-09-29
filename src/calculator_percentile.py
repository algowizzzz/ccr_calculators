from typing import Dict, Any, List
from datetime import datetime, timezone
from cache_store import load_cache, save_cache, save_output

def _nearest_rank_percentile(sorted_vals: List[float], p: float) -> float:
    """
    Nearest-rank percentile per NIST definition:
      rank = ceil(p/100 * N), 1-indexed; return sorted_vals[rank-1]
    """
    if not sorted_vals:
        return None  # caller handles None
    N = len(sorted_vals)
    # clamp p into [0, 100]
    p = max(0.0, min(100.0, float(p)))
    if p == 0:
        return sorted_vals[0]
    rank = int((p/100.0) * N)
    # If (p/100)*N is an integer, nearest-rank uses that; else ceil
    if (p/100.0) * N > rank:
        rank += 1
    rank = max(1, min(N, rank))
    return sorted_vals[rank - 1]

def fv_percentile(trade_id: str) -> Dict[str, Any]:
    """
    Stateless calculator:
      - arg: trade_id only
      - reads:
          cache["trade.fv.matrices"][trade_id] -> 10x10 matrix
          cache["percentile.target"] -> percentile to compute (e.g., 95)
      - returns:
          {"trade.fv.percentile.value": <number|null>, "trade.fv.percentile.ts": <iso>, "trade.fv.percentile.p": <int>}
      - persists result to outputs/ and merges back into cache
    """
    cache: Dict[str, Any] = load_cache()
    matrices = cache.get("trade.fv.matrices", {})
    mat = matrices.get(trade_id)

    p = cache.get("percentile.target", 95)

    # Flatten and compute percentile
    values: List[float] = []
    if isinstance(mat, list):
        for row in mat:
            if isinstance(row, list):
                values.extend(row)

    values = [v for v in values if isinstance(v, (int, float))]

    val = None
    if values:
        values.sort()
        val = _nearest_rank_percentile(values, p)

    ts = datetime.now(timezone.utc).isoformat()
    result: Dict[str, Any] = {
        "trade.fv.percentile.value": val,
        "trade.fv.percentile.ts": ts,
        "trade.fv.percentile.p": int(p)
    }

    # merge and persist
    cache.update(result)
    save_cache(cache)
    save_output(trade_id, result)

    return result
