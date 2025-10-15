from typing import Dict, Any, List
from datetime import datetime, timezone
from cache_store import load_cache, save_cache, save_output

class CCRCalculators:
    """
    CCR (Credit Counterparty Risk) Calculators Class
    
    Contains all stateless calculators that take only trade_id as input:
    1. PFE Max Calculator
    2. FV Percentile Calculator  
    3. Netting Set Calculator (SIM-based PFE)
    4. QUICK PFE Calculator
    5. Combined PFE Calculator (SIM + QUICK)
    6. Limit Matching Calculator
    7. Breach Detection Calculator
    """
    
    @staticmethod
    def _nearest_rank_percentile(sorted_vals: List[float], p: float) -> float:
        """
        Nearest-rank percentile per NIST definition:
          rank = ceil(p/100 * N), 1-indexed; return sorted_vals[rank-1]
        """
        if not sorted_vals:
            return None
        N = len(sorted_vals)
        p = max(0.0, min(100.0, float(p)))
        if p == 0:
            return sorted_vals[0]
        rank = int((p/100.0) * N)
        if (p/100.0) * N > rank:
            rank += 1
        rank = max(1, min(N, rank))
        return sorted_vals[rank - 1]
    
    @classmethod
    def max_trade_value(cls, trade_id: str) -> Dict[str, Any]:
        """
        PFE Max Calculator:
          - Reads PFE vector from cache["trade.vectors"][trade_id]
          - Returns max value with timestamp
        """
        cache: Dict[str, Any] = load_cache()
        vectors = cache.get("trade.vectors", {})
        vector = vectors.get(trade_id, [])

        ts = datetime.now(timezone.utc).isoformat()
        result: Dict[str, Any] = {
            "trade.max.value": (max(vector) if vector else None),
            "trade.max.calc_ts": ts,
        }

        # merge into cache and save
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)

        return result
    
    @classmethod
    def fv_percentile(cls, trade_id: str) -> Dict[str, Any]:
        """
        FV Percentile Calculator:
          - Reads 10x10 FV matrix from cache["trade.fv.matrices"][trade_id]
          - Flattens and computes percentile
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
            val = cls._nearest_rank_percentile(values, p)

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
    
    @classmethod
    def netting_from_trade(cls, trade_id: str) -> Dict[str, Any]:
        """
        Netting Set Calculator:
          1. Identify netting set containing the trade_id
          2. Collect all FV matrices for trades in that netting set
          3. Sum matrices elementwise to create netting matrix
          4. Flatten netting matrix into vector
          5. Compute 95th percentile and max value
        """
        cache = load_cache()
        members_map = cache.get("netting.members", {})
        matrices = cache.get("trade.fv.matrices", {})
        p = int(cache.get("percentile.target", 95))

        # Find the netting set containing this trade
        netting_id = None
        for nid, trades in members_map.items():
            if trade_id in trades:
                netting_id = nid
                break

        if not netting_id:
            ts = datetime.now(timezone.utc).isoformat()
            return {
                "error": f"No netting set found for trade {trade_id}",
                "netting.from_trade.ts": ts
            }

        member_trades = members_map[netting_id]

        # Gather matrices for all trades in the netting set
        valid_matrices = []
        for tid in member_trades:
            if tid in matrices and matrices[tid]:
                valid_matrices.append(matrices[tid])

        if not valid_matrices:
            ts = datetime.now(timezone.utc).isoformat()
            return {
                "error": f"No valid FV matrices found for netting set {netting_id}",
                "netting.from_trade.id": netting_id,
                "netting.from_trade.ts": ts
            }

        # Initialize sum matrix (10x10)
        net_mat = [[0.0] * 10 for _ in range(10)]
        
        # Sum all matrices elementwise
        for matrix in valid_matrices:
            if not matrix or len(matrix) != 10:
                continue
            for i in range(10):
                if not matrix[i] or len(matrix[i]) != 10:
                    continue
                for j in range(10):
                    val = matrix[i][j]
                    if isinstance(val, (int, float)):
                        net_mat[i][j] += val

        # Calculate PFE vector: 95th percentile for each time bucket (column)
        pfe_vector = []
        for t in range(10):  # For each time bucket (column)
            # Extract column t (FV across all scenarios for time bucket t)
            column_values = [net_mat[scenario][t] for scenario in range(10)]
            
            # Sort the distribution for this time bucket
            sorted_vals = sorted(column_values)
            
            # Pluck out the 95th percentile using nearest-rank method
            import math
            N = len(sorted_vals)
            rank = math.ceil(p / 100.0 * N)
            pfe_t = sorted_vals[rank - 1] if sorted_vals else None
            
            pfe_vector.append(pfe_t)

        # Calculate statistics on the PFE vector
        val_percentile = max(pfe_vector) if pfe_vector else None  # Peak PFE
        val_max = max(pfe_vector) if pfe_vector else None  # Same as peak PFE

        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "netting.from_trade.id": netting_id,
            "netting.from_trade.members": member_trades,
            "netting.from_trade.pfe_vector": pfe_vector,
            "netting.from_trade.peak_pfe": val_percentile,
            "netting.from_trade.max_pfe": val_max,
            "netting.from_trade.ts": ts,
            "netting.from_trade.confidence_level": p
        }

        # Persist results
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)

        return result

    @staticmethod
    def quick_pfe(trade_id: str) -> Dict[str, Any]:
        """
        QUICK PFE Calculator: Load pre-calculated QUICK vectors from agreement
        """
        cache = load_cache()
        
        # Load trade data to find agreement
        trades = cache.get("trades", {})
        if trade_id not in trades:
            return {"error": f"Trade {trade_id} not found"}
        
        agreement = trades[trade_id].get("agreement")
        if not agreement:
            return {"error": f"No agreement found for trade {trade_id}"}
        
        # Load QUICK vectors
        quick_data = cache.get("quick_vectors", {})
        if agreement not in quick_data:
            return {"error": f"No QUICK data found for agreement {agreement}"}
        
        quick_info = quick_data[agreement]
        time_buckets = quick_info.get("time_buckets", [])
        
        # Extract PFE vector
        pfe_vector = [bucket.get("pfe", 0.0) for bucket in time_buckets]
        peak_pfe = max(pfe_vector) if pfe_vector else 0.0
        
        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "trade_id": trade_id,
            "agreement": agreement,
            "method": "QUICK",
            "pfe_vector": pfe_vector,
            "peak_pfe": peak_pfe,
            "timestamp": ts
        }
        
        # Persist results
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)
        
        return result

    @staticmethod
    def sim_pfe(trade_id: str) -> Dict[str, Any]:
        """
        SIM PFE Calculator: Calculate 95th percentile per time bucket from scenario matrix
        """
        cache = load_cache()
        
        # Load trade data to find agreement
        trades = cache.get("trades", {})
        if trade_id not in trades:
            return {"error": f"Trade {trade_id} not found"}
        
        agreement = trades[trade_id].get("agreement")
        if not agreement:
            return {"error": f"No agreement found for trade {trade_id}"}
        
        # Load SIM matrices
        sim_data = cache.get("sim_matrices", {})
        if agreement not in sim_data:
            return {"error": f"No SIM data found for agreement {agreement}"}
        
        sim_info = sim_data[agreement]
        scenario_matrix = sim_info.get("scenario_matrix", [])
        
        if not scenario_matrix or len(scenario_matrix) != 10:
            return {"error": f"Invalid scenario matrix for agreement {agreement}"}
        
        # Calculate 95th percentile per time bucket (row)
        pfe_vector = []
        p = 95.0  # 95th percentile
        
        for row in scenario_matrix:  # Each row is a time bucket
            if len(row) != 10:
                continue
            sorted_vals = sorted(row)  # Sort scenarios for this time bucket
            import math
            N = len(sorted_vals)
            rank = math.ceil(p / 100.0 * N)
            pfe_t = sorted_vals[rank - 1] if sorted_vals else 0.0
            pfe_vector.append(pfe_t)
        
        peak_pfe = max(pfe_vector) if pfe_vector else 0.0
        
        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "trade_id": trade_id,
            "agreement": agreement,
            "method": "SIM",
            "pfe_vector": pfe_vector,
            "peak_pfe": peak_pfe,
            "confidence_level": p,
            "timestamp": ts
        }
        
        # Persist results
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)
        
        return result

    @staticmethod
    def combined_pfe(trade_id: str) -> Dict[str, Any]:
        """
        Combined PFE Calculator: SIM + QUICK (element-wise addition)
        """
        # Get SIM PFE
        sim_result = CCRCalculators.sim_pfe(trade_id)
        if "error" in sim_result:
            return sim_result
        
        # Get QUICK PFE
        quick_result = CCRCalculators.quick_pfe(trade_id)
        if "error" in quick_result:
            return quick_result
        
        # Combine vectors element-wise
        sim_vector = sim_result.get("pfe_vector", [])
        quick_vector = quick_result.get("pfe_vector", [])
        
        if len(sim_vector) != len(quick_vector):
            return {"error": "SIM and QUICK vectors have different lengths"}
        
        combined_vector = [sim + quick for sim, quick in zip(sim_vector, quick_vector)]
        peak_pfe = max(combined_vector) if combined_vector else 0.0
        
        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "trade_id": trade_id,
            "agreement": sim_result.get("agreement"),
            "method": "COMBINED",
            "sim_vector": sim_vector,
            "quick_vector": quick_vector,
            "combined_vector": combined_vector,
            "peak_pfe": peak_pfe,
            "timestamp": ts
        }
        
        # Persist results
        cache = load_cache()
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)
        
        return result

    @staticmethod
    def match_limits(trade_id: str) -> Dict[str, Any]:
        """
        Limit Matching Calculator: Find applicable limits for a trade
        """
        cache = load_cache()
        
        # Load trade data
        trades = cache.get("trades", {})
        if trade_id not in trades:
            return {"error": f"Trade {trade_id} not found"}
        
        trade = trades[trade_id]
        
        # Load limits
        limits = cache.get("limits", {})
        if not limits:
            return {"error": "No limits found"}
        
        # Find matching limits
        matched_limits = []
        
        for limit_id, limit_def in limits.items():
            # Check if limit applies (exact match or "ALL")
            applies = True
            
            for field in ["counterparty", "legal_entity", "facility", "sub_product", 
                         "product", "family", "agreement", "country", "connection", 
                         "csa", "netted"]:
                
                limit_value = limit_def.get(field)
                trade_value = trade.get(field)
                
                if limit_value and limit_value != "ALL" and limit_value != trade_value:
                    applies = False
                    break
            
            if applies:
                matched_limits.append({
                    "limit_id": limit_id,
                    "limit_def": limit_def
                })
        
        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "trade_id": trade_id,
            "matched_limits": matched_limits,
            "count": len(matched_limits),
            "timestamp": ts
        }
        
        # Persist results
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)
        
        return result

    @staticmethod
    def check_breaches(trade_id: str) -> Dict[str, Any]:
        """
        Breach Detection Calculator: Compare exposures against limits
        """
        # Get combined PFE
        pfe_result = CCRCalculators.combined_pfe(trade_id)
        if "error" in pfe_result:
            return pfe_result
        
        # Get matched limits
        limits_result = CCRCalculators.match_limits(trade_id)
        if "error" in limits_result:
            return limits_result
        
        combined_vector = pfe_result.get("combined_vector", [])
        matched_limits = limits_result.get("matched_limits", [])
        
        breaches = []
        
        for limit_info in matched_limits:
            limit_def = limit_info["limit_def"]
            limit_id = limit_info["limit_id"]
            buckets = limit_def.get("buckets", [])
            
            for bucket in buckets:
                bucket_range = bucket.get("range", [])
                limit_value = bucket.get("limit", 0)
                
                if len(bucket_range) == 2:
                    start_idx, end_idx = bucket_range
                    # Get max exposure in this bucket range
                    bucket_exposure = max(combined_vector[start_idx:end_idx+1]) if combined_vector else 0.0
                    
                    if bucket_exposure > limit_value:
                        breaches.append({
                            "limit_id": limit_id,
                            "bucket_name": bucket.get("name", f"Bucket {start_idx}-{end_idx}"),
                            "exposure": bucket_exposure,
                            "limit": limit_value,
                            "breach_amount": bucket_exposure - limit_value,
                            "breach_type": "PFE"
                        })
        
        cache = load_cache()
        trades = cache.get("trades", {})
        trade_state = trades.get(trade_id, {}).get("state", "unknown")
        
        # Classify breach severity based on trade state
        for breach in breaches:
            if trade_state == "confirmed":
                breach["severity"] = "VIOLATION"
            elif trade_state in ["reserve", "provision"]:
                breach["severity"] = "RESERVATION_BREACH"
            else:
                breach["severity"] = "UNKNOWN"
        
        ts = datetime.now(timezone.utc).isoformat()
        result = {
            "trade_id": trade_id,
            "trade_state": trade_state,
            "breaches": breaches,
            "breach_count": len(breaches),
            "has_violations": any(b["severity"] == "VIOLATION" for b in breaches),
            "has_reservation_breaches": any(b["severity"] == "RESERVATION_BREACH" for b in breaches),
            "timestamp": ts
        }
        
        # Persist results
        cache.update(result)
        save_cache(cache)
        save_output(trade_id, result)
        
        return result
