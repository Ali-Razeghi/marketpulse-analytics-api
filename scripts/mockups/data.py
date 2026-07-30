"""Deterministic fake data shared by every mockup, so the terminal JSON and
the dashboards always agree with each other.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np


def _round(x: float, n: int = 2) -> float:
    return float(np.round(x, n))


def build_all() -> dict:
    rng = np.random.default_rng(42)
    start = datetime(2026, 6, 27)

    # --- BTC/USD daily series (31 points) --------------------------------
    days = 31
    dates = [start + timedelta(days=i) for i in range(days)]
    steps = rng.normal(120, 900, days)
    btc = 61000 + np.cumsum(steps)
    btc = np.clip(btc, 58000, 70000)
    btc[0] = 61000.0
    btc = np.round(btc, 2)
    btc_ma = _moving_average(btc, 7)

    crypto_summary = {
        "source": "crypto",
        "series_key": "bitcoin/usd",
        "count": days,
        "first_ts": dates[0].strftime("%Y-%m-%dT00:00:00Z"),
        "last_ts": dates[-1].strftime("%Y-%m-%dT00:00:00Z"),
        "first_value": float(btc[0]),
        "last_value": float(btc[-1]),
        "min_value": float(btc.min()),
        "max_value": float(btc.max()),
        "mean_value": _round(btc.mean()),
        "std_value": _round(btc.std(ddof=1)),
        "pct_change": _round((btc[-1] - btc[0]) / btc[0] * 100),
    }

    # --- FX series: USD/EUR and USD/GBP (business days only) --------------
    fx_days = 22
    fx_dates = [start + timedelta(days=i) for i in range(fx_days)]
    eur = 0.92 + np.cumsum(rng.normal(0, 0.0025, fx_days))
    # GBP correlated with EUR plus its own noise.
    gbp = 0.78 + 0.6 * (eur - 0.92) + np.cumsum(rng.normal(0, 0.0015, fx_days))
    eur = np.round(eur, 4)
    gbp = np.round(gbp, 4)
    corr = float(np.corrcoef(eur, gbp)[0, 1])

    correlation = {
        "series_a": "forex:usd/eur",
        "series_b": "forex:usd/gbp",
        "overlapping_points": fx_days,
        "correlation": _round(corr, 3),
    }

    # --- CSV profile ------------------------------------------------------
    columns = [
        # name, dtype, nulls, unique, (min, max, mean) or None
        ("order_id", "int64", 0, 2450, None),
        ("date", "object", 0, 90, None),
        ("region", "object", 4, 5, None),
        ("category", "object", 2, 8, None),
        ("product", "object", 6, 214, None),
        ("quantity", "int64", 0, 19, (1.0, 20.0, 6.42)),
        ("unit_price", "float64", 3, 611, (4.99, 899.0, 128.73)),
        ("revenue", "float64", 5, 2131, (4.99, 8990.0, 742.19)),
        ("discount", "float64", 8, 12, (0.0, 0.35, 0.086)),
        ("customer_id", "int64", 0, 1187, None),
        ("channel", "object", 3, 3, None),
        ("rating", "float64", 7, 6, (1.0, 5.0, 4.13)),
    ]
    col_profiles = []
    for name, dtype, nulls, unique, stats in columns:
        prof = {
            "name": name,
            "dtype": dtype,
            "non_null": 2450 - nulls,
            "nulls": nulls,
            "unique": unique,
            "min": stats[0] if stats else None,
            "max": stats[1] if stats else None,
            "mean": stats[2] if stats else None,
        }
        col_profiles.append(prof)

    total_missing = sum(c[2] for c in columns)  # 38
    csv_profile_full = {
        "dataset_id": "a18c92d0",
        "filename": "sales_data.csv",
        "rows": 2450,
        "columns": 12,
        "missing_values": total_missing,
        "duplicate_rows": 7,
        "column_profiles": col_profiles,
        "status": "processed",
    }
    # Shorter version for the terminal image (first 3 columns only).
    csv_profile_short = dict(csv_profile_full)
    csv_profile_short["column_profiles"] = col_profiles[:3] + ["... (9 more)"]

    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxIiwicm9sZSI6InVzZXIiLCJleHAiOjE3..."
    )

    return {
        "dates": dates,
        "btc": btc,
        "btc_ma": btc_ma,
        "crypto_summary": crypto_summary,
        "fx_dates": fx_dates,
        "eur": eur,
        "gbp": gbp,
        "correlation": correlation,
        "csv_profile_full": csv_profile_full,
        "csv_profile_short": csv_profile_short,
        "columns": columns,
        "token": token,
    }


def _moving_average(a: np.ndarray, window: int) -> np.ndarray:
    out = np.full_like(a, np.nan, dtype=float)
    for i in range(window - 1, len(a)):
        out[i] = a[i - window + 1 : i + 1].mean()
    return out
