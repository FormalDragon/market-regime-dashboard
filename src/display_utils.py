import numpy as np
import pandas as pd

from src.config import ASSET_TYPE_DISPLAY, COUNTRY_DISPLAY, SECTOR_DISPLAY


def fmt_pct(value) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2%}"


def fmt_num(value, digits=2) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.{digits}f}"


def localize_asset_type_value(asset_type: str) -> str:
    return ASSET_TYPE_DISPLAY.get(asset_type, asset_type)


def localize_country_value(country: str) -> str:
    return COUNTRY_DISPLAY.get(country, country)


def localize_sector_value(sector: str) -> str:
    return SECTOR_DISPLAY.get(sector, sector)


def classify_signal_strength(asset_type: str, value: float, metric_type: str = "return") -> str:
    if pd.isna(value):
        return "판정 불가"

    abs_value = abs(value)

    if metric_type == "yield_change":
        if abs_value >= 0.25:
            return "강함"
        if abs_value >= 0.10:
            return "보통"
        return "약함"

    if asset_type == "crypto":
        if abs_value >= 0.15:
            return "강함"
        if abs_value >= 0.05:
            return "보통"
        return "약함"

    if asset_type == "volatility_index":
        if abs_value >= 0.25:
            return "강함"
        if abs_value >= 0.10:
            return "보통"
        return "약함"

    if asset_type in ["equity_index", "sector_index"]:
        if abs_value >= 0.06:
            return "강함"
        if abs_value >= 0.02:
            return "보통"
        return "약함"

    if asset_type in ["safe_asset", "fx", "commodity"]:
        if abs_value >= 0.05:
            return "강함"
        if abs_value >= 0.015:
            return "보통"
        return "약함"

    if abs_value >= 0.06:
        return "강함"
    if abs_value >= 0.02:
        return "보통"
    return "약함"


def score_from_strength(strength: str) -> int:
    if strength == "강함":
        return 2
    if strength in ["보통", "약함"]:
        return 1
    return 0


def relative_strength_label(diff: float) -> str:
    if pd.isna(diff):
        return "판정 불가"

    abs_diff = abs(diff)

    if abs_diff >= 0.06:
        return "강함"
    if abs_diff >= 0.02:
        return "보통"
    return "약함"


def label_asset_signal(row: pd.Series) -> str:
    asset_type = row["asset_type"]
    r30 = row.get("return_30d", np.nan)
    change30 = row.get("change_30d", np.nan)

    if asset_type == "volatility_index":
        if pd.notna(r30) and r30 > 0:
            return "변동성 확대"
        if pd.notna(r30) and r30 < 0:
            return "변동성 완화"
        return "변동성 신호 제한"

    if asset_type in ["equity_index", "sector_index"]:
        if pd.notna(r30) and r30 > 0:
            return "위험자산 강세"
        if pd.notna(r30) and r30 < 0:
            return "위험자산 약세"
        return "주식시장 방향성 제한"

    if asset_type == "safe_asset":
        if pd.notna(r30) and r30 > 0:
            return "안전자산 강세"
        if pd.notna(r30) and r30 < 0:
            return "안전자산 약세"
        return "안전자산 신호 제한"

    if asset_type == "bond_yield":
        if pd.notna(change30) and change30 > 0:
            return "금리 압박"
        if pd.notna(change30) and change30 < 0:
            return "금리 부담 완화"
        return "금리 신호 제한"

    if asset_type == "crypto":
        if pd.notna(r30) and r30 > 0:
            return "고위험 심리 강화"
        if pd.notna(r30) and r30 < 0:
            return "고위험 심리 약화"
        return "고위험 심리 제한"

    if asset_type == "fx":
        if pd.notna(r30) and r30 > 0:
            return "달러 강세"
        if pd.notna(r30) and r30 < 0:
            return "달러 약세"
        return "환율 신호 제한"

    if asset_type == "commodity":
        if pd.notna(r30) and r30 > 0:
            return "원자재 강세"
        if pd.notna(r30) and r30 < 0:
            return "원자재 약세"
        return "원자재 신호 제한"

    return "신호 제한"


def market_meaning_from_signal(row: pd.Series) -> str:
    mapping = {
        "위험자산 강세": "위험 선호 강화",
        "위험자산 약세": "위험 회피 가능성",
        "변동성 확대": "불확실성 확대",
        "변동성 완화": "시장 불안 완화",
        "안전자산 강세": "방어 심리 강화",
        "안전자산 약세": "방어 수요 약화",
        "금리 압박": "유동성 부담",
        "금리 부담 완화": "금리 부담 완화",
        "고위험 심리 강화": "투기적 선호 강화",
        "고위험 심리 약화": "고위험 자산 회피",
        "달러 강세": "방어적 달러 수요",
        "달러 약세": "위험 선호 보조",
        "원자재 강세": "물가·경기 민감 신호",
        "원자재 약세": "수요 둔화 가능성",
    }
    return mapping.get(row["signal_label"], "해석 제한")


def get_notable_assets(snap: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    notable = snap.copy()
    notable["signal_label"] = notable.apply(label_asset_signal, axis=1)
    notable["market_meaning"] = notable.apply(market_meaning_from_signal, axis=1)

    if "z_score_120d" in notable.columns and notable["z_score_120d"].notna().sum() >= top_n:
        notable["notable_score"] = notable["z_score_120d"].abs()
        basis = "120일 이례성 점수"
    else:
        notable["notable_score"] = notable["return_30d"].abs()
        basis = "30일 변화율"

    notable = notable.dropna(subset=["notable_score"])
    notable = notable.sort_values("notable_score", ascending=False).head(top_n)

    result = notable[
        [
            "asset_name",
            "asset_type",
            "return_30d",
            "return_5d",
            "volatility_30d",
            "drawdown_60d",
            "z_score_120d",
            "signal_label",
            "market_meaning",
            "notable_score",
        ]
    ].copy()
    result["selection_basis"] = basis

    return result


def prepare_display_table(
    df: pd.DataFrame,
    percent_columns: list[str] | None = None,
    rename: bool = True,
) -> pd.DataFrame:
    display_df = df.copy()

    if percent_columns:
        for col in percent_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].map(fmt_pct)

    if "z_score_120d" in display_df.columns:
        display_df["z_score_120d"] = display_df["z_score_120d"].map(lambda x: fmt_num(x, 2))

    if "asset_type" in display_df.columns:
        display_df["asset_type"] = display_df["asset_type"].map(localize_asset_type_value)

    if "country" in display_df.columns:
        display_df["country"] = display_df["country"].map(localize_country_value)

    if "sector" in display_df.columns:
        display_df["sector"] = display_df["sector"].map(localize_sector_value)

    if rename:
        display_df = display_df.rename(
            columns={
                "date": "기준일",
                "asset_name": "자산명",
                "asset_type": "자산유형",
                "country": "국가",
                "sector": "섹터",
                "value": "값",
                "return_1d": "1일 변화율",
                "return_5d": "5일 변화율",
                "return_30d": "30일 변화율",
                "volatility_20d": "20일 변동성",
                "volatility_30d": "30일 변동성",
                "drawdown_20d": "20일 낙폭",
                "drawdown_60d": "60일 낙폭",
                "z_score_120d": "120일 이례성 점수",
                "change_5d": "5일 변화폭",
                "change_30d": "30일 변화폭",
                "signal_label": "신호 해석",
                "market_meaning": "시장 의미",
                "selection_basis": "선별 기준",
            }
        )

    return display_df
