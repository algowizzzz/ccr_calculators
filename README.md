# Trade Calculator v2 (Stateless, Cache-Backed)

This enhanced version includes two calculators:
- **PFE Max Calculator**: Computes maximum value from PFE (Potential Future Exposure) vectors
- **FV Percentile Calculator**: Computes percentiles from FV (Fair Value) 10×10 matrices
- Both are **stateless**: take **only** `trade_id` as an argument
- Pull data from a **cache store** with enhanced structure
- Return **JSON** and persist results to `outputs/` and back to the cache

## Layout
```
trade_calc/
  data/
    input.json              # example request payload
    trade_vectors.json      # mock vectors for multiple trades (legacy)
    pfe_vectors.json        # PFE vectors for multiple trades
    fv_matrices.json        # FV 10×10 matrices for multiple trades
  cache/
    cache.json              # runtime cache (includes PFE vectors, FV matrices, percentile config, and latest outputs)
  outputs/
    result_<trade_id>.json  # calculator results saved here
  src/
    cache_store.py          # load/save cache helpers
    calculator_max.py       # PFE max calculator (takes only trade_id)
    calculator_percentile.py # FV percentile calculator (takes only trade_id)
    run_max.py              # convenience runner for PFE max calculator
    run_percentile.py       # convenience runner for FV percentile calculator
  README.md
```

## Quick Start

### PFE Max Calculator
1) Inspect `data/pfe_vectors.json` and `cache/cache.json`.
2) Run the PFE max calculator for a trade id (example: T101):
```bash
python3 src/run_max.py T101
```
3) Result will be printed and stored to `outputs/result_T101.json` and reflected back in `cache/cache.json`.

### FV Percentile Calculator
1) Inspect `data/fv_matrices.json` and `cache/cache.json`.
2) Run the FV percentile calculator for a trade id (example: T202):
```bash
python3 src/run_percentile.py T202
```
3) Result will be printed and stored to `outputs/result_T202.json` and reflected back in `cache/cache.json`.

## Contract

### PFE Max Calculator
- **Input (from cache)**:
  - `trade.pfe.vectors`: `{ "<trade_id>": [numbers...] }`
- **Calculator arg**: only `trade_id: str`
- **Output (JSON)**:
```json
{ "trade.max.value": <number|null>, "trade.max.calc_ts": "<ISO-8601>" }
```

### FV Percentile Calculator
- **Input (from cache)**:
  - `trade.fv.matrices`: `{ "<trade_id>": [[10x10 matrix]] }`
  - `percentile.target`: `<number>` (default: 95)
- **Calculator arg**: only `trade_id: str`
- **Output (JSON)**:
```json
{ "trade.fv.percentile.value": <number|null>, "trade.fv.percentile.ts": "<ISO-8601>", "trade.fv.percentile.p": <int> }
```

## Features
- **Stateless**: Both calculators take only `trade_id` as input
- **Cache-backed**: All data persists in files, survives restarts
- **Dual calculation types**: PFE vectors (max) and FV matrices (percentile)
- **Configurable percentile**: Change `percentile.target` in cache for different percentiles
- **Extensible**: Easy to add more calculators following the same pattern
