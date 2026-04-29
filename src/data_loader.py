import numpy as np
import pandas as pd
import streamlit as st

from src.config import ASSETS, DATA_DIR, DATA_PATH, REQUIRED_ASSET_NAMES


def generate_dummy_data() -> pd.DataFrame:
    DATA_DIR.mkdir(exist_ok=True)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=252)

    rows = []
    rng = np.random.default_rng(42)

    for asset in ASSETS:
        value = float(asset["start"])

        for date in dates:
            asset_type = asset["asset_type"]
            sector = asset["sector"]

            if asset_type == "crypto":
                daily_return = rng.normal(0.0005, 0.035)
            elif asset_type == "volatility_index":
                daily_return = rng.normal(0.0000, 0.045)
            elif asset_type == "bond_yield":
                daily_return = rng.normal(0.0000, 0.005)
            elif asset_type == "sector_index":
                if sector in ["technology", "consumer_discretionary"]:
                    daily_return = rng.normal(0.0005, 0.018)
                elif sector in ["utilities", "consumer_staples", "healthcare"]:
                    daily_return = rng.normal(0.00025, 0.010)
                elif sector in ["energy", "financials"]:
                    daily_return = rng.normal(0.00035, 0.016)
                else:
                    daily_return = rng.normal(0.00035, 0.014)
            elif asset_type in ["safe_asset", "fx", "commodity"]:
                daily_return = rng.normal(0.0002, 0.012)
            else:
                daily_return = rng.normal(0.0004, 0.015)

            value = max(value * (1 + daily_return), 0.0001)

            rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "asset_name": asset["asset_name"],
                    "asset_type": asset["asset_type"],
                    "value": round(value, 4),
                    "country": asset["country"],
                    "sector": asset["sector"],
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
    return df


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return generate_dummy_data()

    df = pd.read_csv(DATA_PATH)

    required_cols = {"date", "asset_name", "asset_type", "value", "country", "sector"}
    missing = required_cols - set(df.columns)

    if missing:
        st.warning("기존 내장 CSV의 스키마가 현재 버전과 맞지 않아 더미 데이터를 재생성합니다.")
        return generate_dummy_data()

    asset_names = set(df["asset_name"].dropna().unique())
    unique_dates = pd.to_datetime(df["date"], errors="coerce").dropna().nunique()

    if not REQUIRED_ASSET_NAMES.issubset(asset_names) or unique_dates < 200:
        st.info("기존 내장 CSV가 1년치/섹터 자산 기준과 맞지 않아 새 더미 데이터를 생성합니다.")
        return generate_dummy_data()

    return df
