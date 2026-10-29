"""
External Financial Data API Tool
Provides live exchange rates and financial benchmark data (inflation, risk-free rate)
with timestamps, source metadata, and deterministic fallback data for offline operation.
"""

import time
import requests
from typing import Dict, Any, Optional

FALLBACK_EXCHANGE_RATES = {
    "base": "INR",
    "timestamp": time.time(),
    "source": "https://open.er-api.com/v6/latest/INR (Offline Fallback)",
    "is_live": False,
    "rates": {
        "USD": 0.012,
        "EUR": 0.011,
        "GBP": 0.0094,
        "AED": 0.044,
        "SGD": 0.016
    }
}

FALLBACK_MARKET_BENCHMARKS = {
    "timestamp": time.time(),
    "source": "Reserve Bank / Standard Benchmarks",
    "is_live": False,
    "inflation_rate_pct": 5.1,
    "repo_rate_pct": 6.5,
    "savings_benchmark_yield_pct": 7.0
}

def get_currency_exchange_rates(base_currency: str = "INR") -> Dict[str, Any]:
    """
    Fetches real-time foreign exchange benchmark rates against base currency.
    Includes timestamps, source metadata, and fallback handling.
    """
    url = f"https://open.er-api.com/v6/latest/{base_currency.upper()}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get("rates", {})
            return {
                "base": base_currency.upper(),
                "timestamp": data.get("time_last_update_unix", time.time()),
                "source": "https://open.er-api.com/v6/latest",
                "is_live": True,
                "rates": {
                    "USD": round(rates.get("USD", 0.012), 4),
                    "EUR": round(rates.get("EUR", 0.011), 4),
                    "GBP": round(rates.get("GBP", 0.0094), 4),
                    "AED": round(rates.get("AED", 0.044), 4),
                    "SGD": round(rates.get("SGD", 0.016), 4)
                }
            }
    except Exception as e:
        print(f"[ExternalFinancialData] FX API request error: {e}. Using offline fallback rates.")

    return FALLBACK_EXCHANGE_RATES

def get_market_benchmarks() -> Dict[str, Any]:
    """
    Returns financial market indicators such as inflation and risk-free benchmarks.
    """
    return FALLBACK_MARKET_BENCHMARKS
