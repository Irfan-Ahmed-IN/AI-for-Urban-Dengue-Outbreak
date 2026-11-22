from bisect import bisect_right
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from threadpoolctl import threadpool_limits

DATA = settings.BASE_DIR / "data"
KEY = ["city", "ward_id"]
NUMERIC = ["population_density_sqkm", "water_logging_risk_index", "sanitation_score",
           "avg_temp_c", "max_temp_c", "min_temp_c", "rainfall_mm", "relative_humidity_pct", "dengue_cases"]
TIERS = ("low", "medium", "high", "critical")


@lru_cache(maxsize=1)
def bundle():
    return joblib.load(settings.BASE_DIR / "ml/multiweek.joblib")


def history():
    path = DATA / "weekly_data.csv"
    return load_history(path, path.stat().st_mtime_ns)


@lru_cache(maxsize=2)
def load_history(path, modified):
    df = pd.read_csv(path, dtype={"ward_id": str, "city": str})
    df.columns = df.columns.str.strip().str.lower()
    df = df[KEY + ["date"] + NUMERIC].copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="raise")
    for col in KEY:
        df[col] = df[col].str.strip()
    if (df.empty or df.isna().any().any() or df[KEY].eq("").any().any()
            or not np.isfinite(df[NUMERIC]).all().all() or df.duplicated(KEY + ["date"]).any()):
        raise ValueError("Invalid ward history")
    df = df.sort_values(KEY + ["date"])
    g = df.groupby(KEY)
    if not g.date.diff().dropna().eq(pd.Timedelta(weeks=1)).all():
        raise ValueError("Expected weekly records")
    for lag in range(1, 5):
        df[f"rainfall_lag_{lag}w"] = g.rainfall_mm.shift(lag)
    df["cases_four_week_mean"] = g.dengue_cases.transform(lambda s: s.rolling(4).mean())
    ready = df.dropna()
    if ready.empty:
        raise ValueError("At least five weeks required")
    return ready


def forecast(row, horizon):
    artifact = bundle()
    target = row.date + pd.Timedelta(weeks=horizon)
    phase = 2 * np.pi * target.dayofyear / 365.25
    inputs = row.to_frame().T.assign(season_sin=np.sin(phase), season_cos=np.cos(phase))
    with threadpool_limits(limits=1, user_api="openmp"):
        estimate = float(artifact["models"][horizon].predict(inputs[artifact["features"]].astype(float))[0])
    return estimate, TIERS[bisect_right(artifact["risk_cutoffs"], estimate)], target
