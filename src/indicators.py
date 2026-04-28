import pandas as pd

from src.config import REGIME_DISPLAY
from src.regime_rules import classify_regime


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df = df.sort_values(["asset_name", "date"])

    df["return_1d"] = df.groupby("asset_name")["value"].pct_change()
    df["return_5d"] = df.groupby("asset_name")["value"].pct_change(5)
    df["return_30d"] = df.groupby("asset_name")["value"].pct_change(30)

    df["change_1d"] = df.groupby("asset_name")["value"].diff()
    df["change_5d"] = df.groupby("asset_name")["value"].diff(5)
    df["change_30d"] = df.groupby("asset_name")["value"].diff(30)

    df["volatility_20d"] = (
        df.groupby("asset_name")["return_1d"]
        .rolling(20)
        .std()
        .reset_index(level=0, drop=True)
    )
    df["volatility_30d"] = (
        df.groupby("asset_name")["return_1d"]
        .rolling(30)
        .std()
        .reset_index(level=0, drop=True)
    )

    rolling_max_20 = (
        df.groupby("asset_name")["value"]
        .rolling(20)
        .max()
        .reset_index(level=0, drop=True)
    )
    rolling_max_60 = (
        df.groupby("asset_name")["value"]
        .rolling(60)
        .max()
        .reset_index(level=0, drop=True)
    )

    df["drawdown_20d"] = (df["value"] - rolling_max_20) / rolling_max_20
    df["drawdown_60d"] = (df["value"] - rolling_max_60) / rolling_max_60

    rolling_mean_120 = (
        df.groupby("asset_name")["return_30d"]
        .rolling(120)
        .mean()
        .reset_index(level=0, drop=True)
    )
    rolling_std_120 = (
        df.groupby("asset_name")["return_30d"]
        .rolling(120)
        .std()
        .reset_index(level=0, drop=True)
    )
    df["z_score_120d"] = (df["return_30d"] - rolling_mean_120) / rolling_std_120

    return df


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values("date")
        .groupby("asset_name", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )


def build_regime_score_history(df: pd.DataFrame, lookback_days: int = 120) -> pd.DataFrame:
    dates = sorted(df["date"].dropna().unique())
    dates = dates[-lookback_days:]

    rows = []

    for date in dates:
        snap_at_date = df[df["date"] == date].copy()
        if snap_at_date.empty:
            continue

        regime, confidence, scores, _, _ = classify_regime(snap_at_date)
        rows.append(
            {
                "date": date,
                "Risk-On": scores["Risk-On"],
                "Risk-Off": scores["Risk-Off"],
                "Tightening Stress": scores["Tightening Stress"],
                "regime": REGIME_DISPLAY.get(regime, regime),
                "confidence": confidence,
            }
        )

    return pd.DataFrame(rows)
