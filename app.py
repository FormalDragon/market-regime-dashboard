"""
글로벌 시장 상태 진단 대시보드

구성:
1. 내장 더미 데이터 생성 및 지표 계산
2. 규칙 기반 시장 상태 분류
3. 신호 강도/패턴 라벨링
4. Streamlit 대시보드 렌더링

주의:
- 투자 추천/매수·매도 판단 목적이 아니라 시장 상태 모니터링용 예시 앱이다.
- 실제 배포 전에는 더미 데이터 대신 검증된 CSV 또는 데이터 수집 스크립트를 연결하는 것을 권장한다.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================
# Page config
# =========================

st.set_page_config(
    page_title="글로벌 시장 상태 진단 대시보드",
    layout="wide",
)

DATA_DIR = Path("data")
DATA_PATH = DATA_DIR / "default_market_indicators.csv"


# =========================
# Built-in demo asset setup
# =========================

ASSETS = [
    # Global / country equity indices
    {"asset_name": "S&P500", "asset_type": "equity_index", "start": 5000, "country": "USA", "sector": "broad_market"},
    {"asset_name": "Nasdaq", "asset_type": "equity_index", "start": 16000, "country": "USA", "sector": "tech_growth"},
    {"asset_name": "KOSPI", "asset_type": "equity_index", "start": 2700, "country": "Korea", "sector": "broad_market"},
    {"asset_name": "Nikkei225", "asset_type": "equity_index", "start": 39000, "country": "Japan", "sector": "broad_market"},
    {"asset_name": "DAX", "asset_type": "equity_index", "start": 18000, "country": "Germany", "sector": "broad_market"},
    {"asset_name": "FTSE100", "asset_type": "equity_index", "start": 7900, "country": "UK", "sector": "broad_market"},
    {"asset_name": "HangSeng", "asset_type": "equity_index", "start": 17000, "country": "Hong Kong", "sector": "broad_market"},
    {"asset_name": "Nifty50", "asset_type": "equity_index", "start": 22000, "country": "India", "sector": "broad_market"},

    # Cross-asset macro signals
    {"asset_name": "Gold", "asset_type": "safe_asset", "start": 2300, "country": "Global", "sector": "precious_metal"},
    {"asset_name": "US10Y", "asset_type": "bond_yield", "start": 4.3, "country": "USA", "sector": "rate"},
    {"asset_name": "VIX", "asset_type": "volatility_index", "start": 18, "country": "USA", "sector": "volatility"},
    {"asset_name": "USD/KRW", "asset_type": "fx", "start": 1350, "country": "Korea", "sector": "fx"},
    {"asset_name": "BTC", "asset_type": "crypto", "start": 65000, "country": "Global", "sector": "crypto"},
    {"asset_name": "Oil", "asset_type": "commodity", "start": 78, "country": "Global", "sector": "energy"},

    # US sector ETF sample data
    {"asset_name": "XLK", "asset_type": "sector_index", "start": 210, "country": "USA", "sector": "technology"},
    {"asset_name": "XLF", "asset_type": "sector_index", "start": 42, "country": "USA", "sector": "financials"},
    {"asset_name": "XLE", "asset_type": "sector_index", "start": 92, "country": "USA", "sector": "energy"},
    {"asset_name": "XLV", "asset_type": "sector_index", "start": 145, "country": "USA", "sector": "healthcare"},
    {"asset_name": "XLP", "asset_type": "sector_index", "start": 76, "country": "USA", "sector": "consumer_staples"},
    {"asset_name": "XLY", "asset_type": "sector_index", "start": 185, "country": "USA", "sector": "consumer_discretionary"},
    {"asset_name": "XLU", "asset_type": "sector_index", "start": 68, "country": "USA", "sector": "utilities"},
    {"asset_name": "XLI", "asset_type": "sector_index", "start": 124, "country": "USA", "sector": "industrials"},
]


REQUIRED_ASSET_NAMES = {asset["asset_name"] for asset in ASSETS}


REGIME_DISPLAY = {
    "Risk-On": "위험 선호",
    "Risk-Off": "위험 회피",
    "Tightening Stress": "금리 압박",
    "Mixed / Uncertain": "방향성 불명확",
}


REGIME_WITH_EN = {
    "Risk-On": "위험 선호(Risk-On)",
    "Risk-Off": "위험 회피(Risk-Off)",
    "Tightening Stress": "금리 압박(Tightening Stress)",
    "Mixed / Uncertain": "방향성 불명확(Mixed)",
}


REGIME_MEANINGS = {
    "Risk-On": "위험자산으로 자금이 이동하는 구간",
    "Risk-Off": "안전자산 또는 방어적 자산으로 자금이 이동하는 구간",
    "Tightening Stress": "금리 상승·달러 강세 등 유동성 부담이 커지는 구간",
    "Mixed / Uncertain": "주요 자산군 신호가 엇갈려 방향성을 단정하기 어려운 구간",
}


ASSET_TYPE_DISPLAY = {
    "equity_index": "주가지수",
    "equity_stock": "개별 주식",
    "sector_index": "섹터·테마",
    "safe_asset": "안전자산",
    "fx": "환율",
    "bond_yield": "채권금리",
    "volatility_index": "변동성 지표",
    "crypto": "암호자산",
    "commodity": "원자재",
    "reit": "리츠·부동산 금융자산",
}


COUNTRY_DISPLAY = {
    "USA": "미국",
    "Korea": "한국",
    "Japan": "일본",
    "Germany": "독일",
    "UK": "영국",
    "Hong Kong": "홍콩",
    "India": "인도",
    "Global": "글로벌",
}


COUNTRY_FLAG = {
    "USA": "🇺🇸",
    "Korea": "🇰🇷",
    "Japan": "🇯🇵",
    "Germany": "🇩🇪",
    "UK": "🇬🇧",
    "Hong Kong": "🇭🇰",
    "India": "🇮🇳",
    "Global": "🌐",
}


SECTOR_DISPLAY = {
    "technology": "기술",
    "financials": "금융",
    "energy": "에너지",
    "healthcare": "헬스케어",
    "consumer_staples": "필수소비재",
    "consumer_discretionary": "임의소비재",
    "utilities": "유틸리티",
    "industrials": "산업재",
    "broad_market": "시장대표",
    "tech_growth": "성장·기술",
    "precious_metal": "귀금속",
    "rate": "금리",
    "volatility": "변동성",
    "fx": "환율",
    "crypto": "암호자산",
}


MAX_SCORES = {
    "Risk-On": 16,
    "Risk-Off": 16,
    "Tightening Stress": 14,
}


# =========================
# Data functions
# =========================

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


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df = df.sort_values(["asset_name", "date"])

    df["return_1d"] = df.groupby("asset_name")["value"].pct_change()
    df["return_5d"] = df.groupby("asset_name")["value"].pct_change(5)
    df["return_30d"] = df.groupby("asset_name")["value"].pct_change(30)

    # 채권금리는 수익률보다 금리 변화폭 중심으로 해석한다.
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


# =========================
# Regime classification
# =========================

def classify_regime(snap: pd.DataFrame):
    scores = {
        "Risk-On": 0,
        "Risk-Off": 0,
        "Tightening Stress": 0,
    }

    evidence = {
        "Risk-On": [],
        "Risk-Off": [],
        "Tightening Stress": [],
    }

    rule_checks = {
        "Risk-On": [],
        "Risk-Off": [],
        "Tightening Stress": [],
    }

    def get_row(asset_name: str):
        result = snap[snap["asset_name"] == asset_name]
        if result.empty:
            return None
        return result.iloc[0]

    def add_rule(
        regime_name: str,
        criterion: str,
        matched: bool,
        strength: str = "약함",
        base_score: int | None = None,
    ):
        if matched:
            score = base_score if base_score is not None else score_from_strength(strength)
            scores[regime_name] += score
            evidence[regime_name].append(criterion)
        else:
            score = 0
            strength = "해당 없음"

        rule_checks[regime_name].append(
            {
                "criterion": criterion,
                "matched": matched,
                "strength": strength,
                "score": score,
            }
        )

    sp = get_row("S&P500")
    nasdaq = get_row("Nasdaq")
    btc = get_row("BTC")
    gold = get_row("Gold")
    vix = get_row("VIX")
    us10y = get_row("US10Y")
    usdkrw = get_row("USD/KRW")
    xlk = get_row("XLK")
    xlu = get_row("XLU")
    xlp = get_row("XLP")

    # =========================
    # Risk-On rules
    # =========================

    if sp is not None and pd.notna(sp["return_30d"]):
        add_rule(
            "Risk-On",
            "S&P500 30일 변화율 상승",
            sp["return_30d"] > 0,
            classify_signal_strength("equity_index", sp["return_30d"]),
        )

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule(
            "Risk-On",
            "Nasdaq 30일 변화율 상승",
            nasdaq["return_30d"] > 0,
            classify_signal_strength("equity_index", nasdaq["return_30d"]),
        )

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule(
            "Risk-On",
            "BTC 30일 변화율 상승",
            btc["return_30d"] > 0,
            classify_signal_strength("crypto", btc["return_30d"]),
        )

    if vix is not None and pd.notna(vix["return_30d"]):
        add_rule(
            "Risk-On",
            "VIX 30일 변화율 하락",
            vix["return_30d"] < 0,
            classify_signal_strength("volatility_index", vix["return_30d"]),
        )

    if gold is not None and sp is not None and pd.notna(gold["return_30d"]) and pd.notna(sp["return_30d"]):
        diff = sp["return_30d"] - gold["return_30d"]
        add_rule(
            "Risk-On",
            "Gold가 S&P500 대비 30일 상대약세",
            gold["return_30d"] < sp["return_30d"],
            relative_strength_label(diff),
        )

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule(
            "Risk-On",
            "USD/KRW 30일 변화율 하락",
            usdkrw["return_30d"] < 0,
            classify_signal_strength("fx", usdkrw["return_30d"]),
        )

    if xlk is not None and xlu is not None and pd.notna(xlk["return_30d"]) and pd.notna(xlu["return_30d"]):
        diff = xlk["return_30d"] - xlu["return_30d"]
        add_rule(
            "Risk-On",
            "기술 섹터가 방어 섹터 대비 강세",
            xlk["return_30d"] > xlu["return_30d"],
            relative_strength_label(diff),
        )

    if sp is not None and pd.notna(sp["return_5d"]):
        add_rule(
            "Risk-On",
            "S&P500 5일 변화율 +2% 이상 단기 강세",
            sp["return_5d"] > 0.02,
            classify_signal_strength("equity_index", sp["return_5d"]),
        )

    # =========================
    # Risk-Off rules
    # =========================

    if sp is not None and pd.notna(sp["return_30d"]):
        add_rule(
            "Risk-Off",
            "S&P500 30일 변화율 하락",
            sp["return_30d"] < 0,
            classify_signal_strength("equity_index", sp["return_30d"]),
        )

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule(
            "Risk-Off",
            "Nasdaq 30일 변화율 하락",
            nasdaq["return_30d"] < 0,
            classify_signal_strength("equity_index", nasdaq["return_30d"]),
        )

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule(
            "Risk-Off",
            "BTC 30일 변화율 하락",
            btc["return_30d"] < 0,
            classify_signal_strength("crypto", btc["return_30d"]),
        )

    if vix is not None and pd.notna(vix["return_30d"]):
        add_rule(
            "Risk-Off",
            "VIX 30일 변화율 상승",
            vix["return_30d"] > 0,
            classify_signal_strength("volatility_index", vix["return_30d"]),
        )

    if gold is not None and sp is not None and pd.notna(gold["return_30d"]) and pd.notna(sp["return_30d"]):
        diff = gold["return_30d"] - sp["return_30d"]
        add_rule(
            "Risk-Off",
            "Gold가 S&P500 대비 30일 상대강세",
            gold["return_30d"] > sp["return_30d"],
            relative_strength_label(diff),
        )

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule(
            "Risk-Off",
            "USD/KRW 30일 변화율 상승",
            usdkrw["return_30d"] > 0,
            classify_signal_strength("fx", usdkrw["return_30d"]),
        )

    if xlk is not None and xlu is not None and pd.notna(xlk["return_30d"]) and pd.notna(xlu["return_30d"]):
        diff = xlu["return_30d"] - xlk["return_30d"]
        add_rule(
            "Risk-Off",
            "방어 섹터가 기술 섹터 대비 강세",
            xlu["return_30d"] > xlk["return_30d"],
            relative_strength_label(diff),
        )

    if sp is not None and pd.notna(sp["return_5d"]):
        add_rule(
            "Risk-Off",
            "S&P500 5일 변화율 -2% 이하 단기 급락",
            sp["return_5d"] < -0.02,
            classify_signal_strength("equity_index", sp["return_5d"]),
        )

    # =========================
    # Tightening Stress rules
    # =========================

    if us10y is not None and pd.notna(us10y["change_30d"]):
        add_rule(
            "Tightening Stress",
            "US10Y 금리 30일 변화폭 상승",
            us10y["change_30d"] > 0,
            classify_signal_strength("bond_yield", us10y["change_30d"], metric_type="yield_change"),
        )

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule(
            "Tightening Stress",
            "Nasdaq 30일 변화율 하락",
            nasdaq["return_30d"] < 0,
            classify_signal_strength("equity_index", nasdaq["return_30d"]),
        )

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule(
            "Tightening Stress",
            "USD/KRW 30일 변화율 상승",
            usdkrw["return_30d"] > 0,
            classify_signal_strength("fx", usdkrw["return_30d"]),
        )

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule(
            "Tightening Stress",
            "BTC 30일 변화율 하락",
            btc["return_30d"] < 0,
            classify_signal_strength("crypto", btc["return_30d"]),
        )

    if xlk is not None and pd.notna(xlk["return_30d"]):
        add_rule(
            "Tightening Stress",
            "기술 섹터 30일 약세",
            xlk["return_30d"] < 0,
            classify_signal_strength("sector_index", xlk["return_30d"]),
        )

    if xlp is not None and xlk is not None and pd.notna(xlp["return_30d"]) and pd.notna(xlk["return_30d"]):
        diff = xlp["return_30d"] - xlk["return_30d"]
        add_rule(
            "Tightening Stress",
            "필수소비재가 기술 섹터 대비 강세",
            xlp["return_30d"] > xlk["return_30d"],
            relative_strength_label(diff),
        )

    if us10y is not None and pd.notna(us10y["change_5d"]):
        add_rule(
            "Tightening Stress",
            "US10Y 금리 5일 변화폭 상승",
            us10y["change_5d"] > 0,
            classify_signal_strength("bond_yield", us10y["change_5d"], metric_type="yield_change"),
        )

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_regime, top_score = sorted_scores[0]
    _, second_score = sorted_scores[1]
    score_gap = top_score - second_score

    if top_score <= 4 or score_gap <= 1:
        regime = "Mixed / Uncertain"
    else:
        regime = top_regime

    top_max_score = MAX_SCORES.get(top_regime, 16)
    confidence = min(round((top_score / top_max_score) * 100), 100)

    return regime, confidence, scores, evidence, rule_checks


def flatten_evidence(evidence: dict[str, list[str]]) -> list[str]:
    seen = set()
    signals = []
    for items in evidence.values():
        for item in items:
            if item not in seen:
                seen.add(item)
                signals.append(item)
    return signals


def build_dominant_signal(evidence: dict[str, list[str]]) -> str:
    text = " ".join(flatten_evidence(evidence))
    keywords = []

    if "S&P500 30일 변화율 하락" in text or "Nasdaq 30일 변화율 하락" in text:
        keywords.append("주식 약세")
    if "S&P500 30일 변화율 상승" in text or "Nasdaq 30일 변화율 상승" in text:
        keywords.append("주식 강세")
    if "VIX 30일 변화율 상승" in text:
        keywords.append("변동성 확대")
    if "VIX 30일 변화율 하락" in text:
        keywords.append("변동성 완화")
    if "USD/KRW 30일 변화율 상승" in text:
        keywords.append("달러 강세")
    if "USD/KRW 30일 변화율 하락" in text:
        keywords.append("달러 약세")
    if "US10Y" in text:
        keywords.append("금리 압박")
    if "Gold" in text and "상대강세" in text:
        keywords.append("안전자산 강세")
    if "기술 섹터" in text and "약세" in text:
        keywords.append("기술주 약세")
    if "방어 섹터" in text:
        keywords.append("방어 섹터 강세")
    if "BTC 30일 변화율 하락" in text:
        keywords.append("고위험 자산 약세")
    if "BTC 30일 변화율 상승" in text:
        keywords.append("고위험 자산 강세")

    if not keywords:
        return "뚜렷한 핵심 신호 제한"

    return " + ".join(keywords[:3])


def generate_insight(regime: str, dominant_signal: str) -> str:
    display_regime = REGIME_DISPLAY.get(regime, regime)

    if regime == "Risk-Off":
        return (
            f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. "
            f"핵심 신호는 **{dominant_signal}**입니다. "
            f"최근 30일 기준 위험자산 약세와 방어적 신호가 함께 관찰되며, "
            f"시장 참여자의 위험 회피 성향이 강화된 구간으로 해석됩니다."
        )

    if regime == "Risk-On":
        return (
            f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. "
            f"핵심 신호는 **{dominant_signal}**입니다. "
            f"최근 30일 기준 위험자산 선호와 변동성 완화 신호가 관찰되며, "
            f"시장 참여자의 위험 감수 성향이 강화된 구간으로 해석됩니다."
        )

    if regime == "Tightening Stress":
        return (
            f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. "
            f"핵심 신호는 **{dominant_signal}**입니다. "
            f"최근 30일 기준 금리 상승, 달러 강세, 성장주 약세가 함께 나타나는지 확인할 필요가 있습니다. "
            f"이는 유동성 부담이 시장에 반영되는 구간으로 해석됩니다."
        )

    return (
        f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. "
        f"핵심 신호는 **{dominant_signal}**입니다. "
        f"최근 30일 기준 주요 자산군 간 신호가 엇갈리거나 상태 점수 차이가 충분하지 않습니다. "
        f"따라서 특정 방향으로 단정하기보다 방향성이 불명확한 구간으로 해석합니다."
    )


# =========================
# Display helpers
# =========================

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
    """
    수치 변화의 크기를 약함 / 보통 / 강함으로 분류한다.
    metric_type:
    - return: 수익률/변화율 기준
    - yield_change: 금리 변화폭 기준
    """

    if pd.isna(value):
        return "판정 불가"

    abs_value = abs(value)

    if metric_type == "yield_change":
        # US10Y 같은 금리 레벨 변화폭. 단위는 %p 수준의 값으로 가정.
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
    """
    신호 강도에 따른 점수 가중치.
    강함: +2
    보통/약함: +1
    미충족/판정 불가: 0
    """

    if strength == "강함":
        return 2
    if strength in ["보통", "약함"]:
        return 1
    return 0


def relative_strength_label(diff: float) -> str:
    """
    두 자산 간 상대강도 차이 기준.
    예: Gold return_30d - S&P500 return_30d
    """

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


def build_score_cards_df(scores: dict[str, int]) -> pd.DataFrame:
    rows = []

    for regime_name, score in scores.items():
        rows.append(
            {
                "regime": regime_name,
                "display_name": REGIME_DISPLAY.get(regime_name, regime_name),
                "display_with_en": REGIME_WITH_EN.get(regime_name, regime_name),
                "score": score,
                "max_score": MAX_SCORES.get(regime_name, 0),
                "meaning": REGIME_MEANINGS.get(regime_name, "-"),
            }
        )

    return pd.DataFrame(rows).sort_values("score", ascending=False)


def build_confidence_details(scores: dict[str, int], confidence: int) -> dict:
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_regime, top_score = sorted_scores[0]
    second_regime, second_score = sorted_scores[1]
    score_gap = top_score - second_score

    if confidence >= 75 and score_gap >= 2:
        confidence_label = "비교적 명확한 판정"
    elif confidence >= 50:
        confidence_label = "중간 수준의 판정"
    else:
        confidence_label = "제한적 판정"

    return {
        "top_regime": top_regime,
        "top_score": top_score,
        "second_regime": second_regime,
        "second_score": second_score,
        "score_gap": score_gap,
        "confidence": confidence,
        "confidence_label": confidence_label,
    }


def render_confidence_gauge(confidence_details: dict):
    confidence = confidence_details["confidence"]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=confidence,
            number={"suffix": "%", "font": {"size": 38}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4f46e5"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 75], "color": "#fef3c7"},
                    {"range": [75, 100], "color": "#dcfce7"},
                ],
            },
            title={"text": "판정 신뢰도"},
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        f"""
**{confidence_details["confidence_label"]}**

- 최고 점수 상태: **{REGIME_WITH_EN.get(confidence_details["top_regime"], confidence_details["top_regime"])}**
- 최고 점수: **{confidence_details["top_score"]}점**
- 차순위 상태: **{REGIME_WITH_EN.get(confidence_details["second_regime"], confidence_details["second_regime"])}**
- 점수 차이: **{confidence_details["score_gap"]}점**
"""
    )


def render_regime_score_cards(score_cards_df: pd.DataFrame):
    cols = st.columns(3)

    for idx, (_, row) in enumerate(score_cards_df.iterrows()):
        with cols[idx % 3]:
            st.metric(
                label=row["display_name"],
                value=f"{row['score']} / {row['max_score']}",
                help=row["display_with_en"],
            )
            st.caption(row["meaning"])


def render_notable_asset_cards(notable_assets: pd.DataFrame):
    cards = notable_assets.head(5).copy()

    if cards.empty:
        st.info("주요 이슈 자산을 표시할 데이터가 부족합니다.")
        return

    cols = st.columns(len(cards))

    for idx, (_, row) in enumerate(cards.iterrows()):
        with cols[idx]:
            asset_type = localize_asset_type_value(row["asset_type"])
            st.markdown(f"#### {row['asset_name']}")
            st.metric(
                label=asset_type,
                value=fmt_pct(row["return_30d"]),
                delta=f"5일 {fmt_pct(row['return_5d'])}",
            )
            st.caption(f"{row['signal_label']} · {row['market_meaning']}")
            if pd.notna(row.get("z_score_120d")):
                st.caption(f"120일 이례성 점수: {fmt_num(row['z_score_120d'])}")


def build_overview_metrics(snap: pd.DataFrame) -> dict:
    risk_assets = snap[snap["asset_type"].isin(["equity_index", "sector_index", "crypto"])]
    defensive_assets = snap[snap["asset_type"].isin(["safe_asset"])]

    risk_avg = risk_assets["return_30d"].mean()
    defensive_avg = defensive_assets["return_30d"].mean()

    vix_row = snap[snap["asset_name"] == "VIX"]
    us10y_row = snap[snap["asset_name"] == "US10Y"]

    vix_change = vix_row["return_30d"].iloc[0] if not vix_row.empty else np.nan
    us10y_change = us10y_row["change_30d"].iloc[0] if not us10y_row.empty else np.nan

    equity = snap[snap["asset_type"] == "equity_index"]
    falling_markets = int((equity["return_30d"] < -0.005).sum())

    max_move_row = snap.dropna(subset=["return_30d"]).copy()
    if max_move_row.empty:
        max_asset = "-"
        max_move = np.nan
    else:
        max_move_row["abs_return"] = max_move_row["return_30d"].abs()
        picked = max_move_row.sort_values("abs_return", ascending=False).iloc[0]
        max_asset = picked["asset_name"]
        max_move = picked["return_30d"]

    return {
        "risk_avg": risk_avg,
        "defensive_avg": defensive_avg,
        "vix_change": vix_change,
        "us10y_change": us10y_change,
        "falling_markets": falling_markets,
        "max_asset": max_asset,
        "max_move": max_move,
    }


def render_overview_metric_cards(metrics: dict):
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("위험자산 30일 평균", fmt_pct(metrics["risk_avg"]))
    col2.metric("방어자산 30일 평균", fmt_pct(metrics["defensive_avg"]))
    col3.metric("VIX 30일 변화", fmt_pct(metrics["vix_change"]))
    col4.metric("US10Y 30일 변화폭", f"{metrics['us10y_change']:.3f}" if pd.notna(metrics["us10y_change"]) else "-")
    col5.metric("최대 변동 자산", metrics["max_asset"], fmt_pct(metrics["max_move"]))
    col6.metric("하락 주식시장", f"{metrics['falling_markets']}개")


def render_regime_rule_cards(rule_checks: dict[str, list[dict]], scores: dict[str, int]):
    cols = st.columns(3)
    regime_order = ["Risk-On", "Risk-Off", "Tightening Stress"]

    for idx, regime_name in enumerate(regime_order):
        with cols[idx]:
            display_name = REGIME_WITH_EN.get(regime_name, regime_name)
            score = scores.get(regime_name, 0)
            max_score = MAX_SCORES.get(regime_name, 0)
            meaning = REGIME_MEANINGS.get(regime_name, "-")

            st.markdown(f"#### {display_name}")
            st.metric("점수", f"{score} / {max_score}")
            st.caption(meaning)

            for rule in rule_checks.get(regime_name, []):
                check = "✅" if rule["matched"] else "❌"
                score_text = f"+{rule['score']}" if rule["matched"] else "0"
                strength = rule.get("strength", "해당 없음")

                if rule["matched"]:
                    st.write(f"{check} {rule['criterion']} · 강도: **{strength}** ({score_text})")
                else:
                    st.write(f"{check} {rule['criterion']} ({score_text})")


def has_matched_rule(rule_checks: dict[str, list[dict]], regime_name: str, keyword: str) -> bool:
    return any(
        rule["matched"] and keyword in rule["criterion"]
        for rule in rule_checks.get(regime_name, [])
    )


def matched_strength(rule_checks: dict[str, list[dict]], regime_name: str, keyword: str) -> str:
    for rule in rule_checks.get(regime_name, []):
        if rule["matched"] and keyword in rule["criterion"]:
            return rule.get("strength", "약함")
    return "해당 없음"


def pattern_strength_from_rules(strengths: list[str]) -> str:
    valid = [s for s in strengths if s in ["약함", "보통", "강함"]]

    if not valid:
        return "약함"

    strong_count = valid.count("강함")
    medium_count = valid.count("보통")

    if strong_count >= 2:
        return "강함"
    if strong_count == 1 or medium_count >= 2:
        return "보통"
    return "약함"


def detect_market_patterns(
    rule_checks: dict[str, list[dict]],
    country_df: pd.DataFrame,
    sector_df: pd.DataFrame,
) -> list[dict]:
    patterns = []

    # 1. 전형적 위험 회피 패턴
    risk_off_core = [
        has_matched_rule(rule_checks, "Risk-Off", "S&P500 30일 변화율 하락"),
        has_matched_rule(rule_checks, "Risk-Off", "VIX 30일 변화율 상승"),
        has_matched_rule(rule_checks, "Risk-Off", "Gold가 S&P500 대비 30일 상대강세"),
    ]

    if sum(risk_off_core) >= 2:
        strengths = [
            matched_strength(rule_checks, "Risk-Off", "S&P500"),
            matched_strength(rule_checks, "Risk-Off", "VIX"),
            matched_strength(rule_checks, "Risk-Off", "Gold"),
        ]
        patterns.append(
            {
                "name": "전형적 위험 회피 패턴",
                "strength": pattern_strength_from_rules(strengths),
                "basis": "주식 약세, 변동성 확대, 안전자산 상대강세 조건 중 다수가 충족되었습니다.",
            }
        )

    # 2. 금리 압박형 약세 패턴
    tightening_core = [
        has_matched_rule(rule_checks, "Tightening Stress", "US10Y 금리 30일 변화폭 상승"),
        has_matched_rule(rule_checks, "Tightening Stress", "Nasdaq 30일 변화율 하락"),
        has_matched_rule(rule_checks, "Tightening Stress", "기술 섹터 30일 약세"),
    ]

    if sum(tightening_core) >= 2:
        strengths = [
            matched_strength(rule_checks, "Tightening Stress", "US10Y"),
            matched_strength(rule_checks, "Tightening Stress", "Nasdaq"),
            matched_strength(rule_checks, "Tightening Stress", "기술 섹터"),
        ]
        patterns.append(
            {
                "name": "금리 압박형 약세 패턴",
                "strength": pattern_strength_from_rules(strengths),
                "basis": "금리 상승, 성장주 약세, 기술 섹터 약세 조건 중 다수가 충족되었습니다.",
            }
        )

    # 3. 위험 선호 확산 패턴
    risk_on_core = [
        has_matched_rule(rule_checks, "Risk-On", "S&P500 30일 변화율 상승"),
        has_matched_rule(rule_checks, "Risk-On", "Nasdaq 30일 변화율 상승"),
        has_matched_rule(rule_checks, "Risk-On", "BTC 30일 변화율 상승"),
        has_matched_rule(rule_checks, "Risk-On", "VIX 30일 변화율 하락"),
    ]

    if sum(risk_on_core) >= 3:
        strengths = [
            matched_strength(rule_checks, "Risk-On", "S&P500"),
            matched_strength(rule_checks, "Risk-On", "Nasdaq"),
            matched_strength(rule_checks, "Risk-On", "BTC"),
            matched_strength(rule_checks, "Risk-On", "VIX"),
        ]
        patterns.append(
            {
                "name": "위험 선호 확산 패턴",
                "strength": pattern_strength_from_rules(strengths),
                "basis": "주식, 고위험 자산, 변동성 완화 조건이 함께 관찰되었습니다.",
            }
        )

    # 4. 방어적 섹터 로테이션
    if not sector_df.empty:
        defensive = sector_df[sector_df["sector"].isin(["utilities", "consumer_staples", "healthcare"])]
        growth = sector_df[sector_df["sector"].isin(["technology", "consumer_discretionary"])]

        defensive_avg = defensive["return_30d"].mean()
        growth_avg = growth["return_30d"].mean()

        if pd.notna(defensive_avg) and pd.notna(growth_avg) and defensive_avg > growth_avg:
            diff = defensive_avg - growth_avg
            strength = relative_strength_label(diff)
            patterns.append(
                {
                    "name": "방어적 섹터 로테이션",
                    "strength": strength,
                    "basis": f"방어 섹터 평균 30일 변화율({fmt_pct(defensive_avg)})이 성장 섹터({fmt_pct(growth_avg)})보다 높습니다.",
                }
            )

    # 5. 지역 약세 확산
    if not country_df.empty:
        falling_count = int((country_df["market_status"] == "하락").sum())
        total_count = len(country_df)

        if total_count > 0 and falling_count / total_count >= 0.6:
            patterns.append(
                {
                    "name": "지역 주식시장 약세 확산",
                    "strength": "보통" if falling_count < total_count else "강함",
                    "basis": f"주요 국가 대표 지수 {total_count}개 중 {falling_count}개가 30일 기준 하락으로 분류되었습니다.",
                }
            )

    if not patterns:
        patterns.append(
            {
                "name": "뚜렷한 복합 패턴 제한",
                "strength": "약함",
                "basis": "주요 자산군 신호가 특정 패턴으로 충분히 결합되지 않았습니다.",
            }
        )

    return patterns


def render_market_pattern_cards(patterns: list[dict]):
    st.markdown("### 감지된 시장 패턴")
    st.caption("사전에 정의한 규칙 조합을 기준으로, 현재 관찰되는 시장 패턴을 표시합니다.")

    cols = st.columns(min(3, len(patterns)))

    for idx, pattern in enumerate(patterns):
        with cols[idx % len(cols)]:
            st.markdown(f"#### {pattern['name']}")
            st.metric("패턴 강도", pattern["strength"])
            st.caption(pattern["basis"])


# =========================
# Regional / sector boards
# =========================

def build_global_regional_alignment(regime: str, country_df: pd.DataFrame) -> dict:
    if country_df.empty:
        return {
            "label": "판정 제한",
            "description": "국가별 주식시장 반응 데이터가 부족합니다.",
        }

    total = len(country_df)
    rising = int((country_df["market_status"] == "상승").sum())
    falling = int((country_df["market_status"] == "하락").sum())
    neutral = int((country_df["market_status"] == "보합").sum())

    if regime == "Risk-Off":
        if falling / total >= 0.6:
            label = "글로벌 신호와 지역 반응 일치"
            description = f"현재 글로벌 상태는 위험 회피이며, 주요 국가 {total}개 중 {falling}개가 하락으로 분류되어 지역 주식시장 반응도 같은 방향으로 관찰됩니다."
        else:
            label = "글로벌 신호와 지역 반응 일부 불일치"
            description = f"현재 글로벌 상태는 위험 회피이지만, 국가별 반응은 상승 {rising}개, 보합 {neutral}개, 하락 {falling}개로 분산되어 있습니다."

    elif regime == "Risk-On":
        if rising / total >= 0.6:
            label = "글로벌 신호와 지역 반응 일치"
            description = f"현재 글로벌 상태는 위험 선호이며, 주요 국가 {total}개 중 {rising}개가 상승으로 분류되어 지역 주식시장 반응도 같은 방향으로 관찰됩니다."
        else:
            label = "글로벌 신호와 지역 반응 일부 불일치"
            description = f"현재 글로벌 상태는 위험 선호이지만, 국가별 반응은 상승 {rising}개, 보합 {neutral}개, 하락 {falling}개로 분산되어 있습니다."

    elif regime == "Tightening Stress":
        label = "금리 압박 신호와 지역 반응 확인 필요"
        description = f"현재 글로벌 상태는 금리 압박으로 분류되었습니다. 국가별 주식시장 반응은 상승 {rising}개, 보합 {neutral}개, 하락 {falling}개입니다."

    else:
        label = "방향성 불명확"
        description = f"현재 글로벌 상태가 방향성 불명확으로 분류되어, 지역 반응도 상승 {rising}개, 보합 {neutral}개, 하락 {falling}개로 함께 확인해야 합니다."

    return {
        "label": label,
        "description": description,
    }


def render_global_regional_alignment(alignment: dict):
    st.markdown("### 글로벌-지역 반응 일치도")
    st.metric("판정", alignment["label"])
    st.caption(alignment["description"])


def country_reaction_text(row: pd.Series) -> str:
    status = row["market_status"]
    if status == "상승":
        return "상대적 강세가 관찰됩니다."
    if status == "하락":
        return "약세 반응이 관찰됩니다."
    return "방향성이 제한적입니다."


def build_country_reaction_df(snap: pd.DataFrame) -> pd.DataFrame:
    equity = snap[snap["asset_type"] == "equity_index"].copy()
    equity = equity[~equity["country"].isin(["Global"])]

    threshold = 0.005
    equity["market_status"] = np.select(
        [
            equity["return_30d"] > threshold,
            equity["return_30d"] < -threshold,
        ],
        ["상승", "하락"],
        default="보합",
    )

    equity["country_display"] = equity["country"].map(localize_country_value)
    equity["flag"] = equity["country"].map(lambda x: COUNTRY_FLAG.get(x, "🏳️"))
    equity["reaction_text"] = equity.apply(country_reaction_text, axis=1)

    return equity.sort_values("return_30d", ascending=False)


def render_country_cards(country_df: pd.DataFrame):
    if country_df.empty:
        st.info("국가별 주식시장 반응을 표시할 데이터가 부족합니다.")
        return

    rising_count = int((country_df["market_status"] == "상승").sum())
    neutral_count = int((country_df["market_status"] == "보합").sum())
    falling_count = int((country_df["market_status"] == "하락").sum())

    strongest = country_df.sort_values("return_30d", ascending=False).iloc[0]
    weakest = country_df.sort_values("return_30d", ascending=True).iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("상승 시장", f"{rising_count}개")
    col2.metric("보합 시장", f"{neutral_count}개")
    col3.metric("하락 시장", f"{falling_count}개")
    col4.metric("가장 강한 시장", strongest["country_display"], fmt_pct(strongest["return_30d"]))
    col5.metric("가장 약한 시장", weakest["country_display"], fmt_pct(weakest["return_30d"]))

    st.markdown("### 국가별 시장 반응")

    rows = [country_df.iloc[i:i + 3] for i in range(0, len(country_df), 3)]
    for row_group in rows:
        cols = st.columns(3)
        for col, (_, row) in zip(cols, row_group.iterrows()):
            with col:
                st.markdown(f"#### {row['flag']} {row['country_display']}")
                st.metric(
                    label=row["asset_name"],
                    value=fmt_pct(row["return_30d"]),
                    delta=f"5일 {fmt_pct(row['return_5d'])}",
                )
                st.caption(row["reaction_text"])
                st.caption(f"30일 변동성: {fmt_pct(row['volatility_30d'])} · 60일 낙폭: {fmt_pct(row['drawdown_60d'])}")


def render_country_ranking(country_df: pd.DataFrame):
    st.markdown("### 국가별 변화율 순위")

    fig = px.bar(
        country_df.sort_values("return_30d"),
        x="return_30d",
        y="country_display",
        color="return_30d",
        orientation="h",
        color_continuous_scale=[
            (0.0, "blue"),
            (0.5, "white"),
            (1.0, "red"),
        ],
        color_continuous_midpoint=0,
        labels={"return_30d": "30일 변화율", "country_display": "국가"},
        title="국가별 대표 주가지수 30일 변화율",
    )
    fig.update_xaxes(tickformat=".1%")
    fig.update_layout(height=430)
    st.plotly_chart(fig, width="stretch")


def build_sector_reaction_df(snap: pd.DataFrame) -> pd.DataFrame:
    sector_df = snap[snap["asset_type"] == "sector_index"].copy()
    sector_df["sector_display"] = sector_df["sector"].map(localize_sector_value)
    sector_df["signal_label"] = sector_df.apply(label_asset_signal, axis=1)
    sector_df["market_meaning"] = sector_df.apply(market_meaning_from_signal, axis=1)
    return sector_df.sort_values("return_30d", ascending=False)


def build_sector_rotation_summary(sector_df: pd.DataFrame) -> dict:
    if sector_df.empty:
        return {
            "label": "판정 제한",
            "description": "섹터 데이터가 부족합니다.",
        }

    growth = sector_df[sector_df["sector"].isin(["technology", "consumer_discretionary"])]
    defensive = sector_df[sector_df["sector"].isin(["utilities", "consumer_staples", "healthcare"])]
    cyclical = sector_df[sector_df["sector"].isin(["financials", "energy", "industrials"])]

    growth_avg = growth["return_30d"].mean()
    defensive_avg = defensive["return_30d"].mean()
    cyclical_avg = cyclical["return_30d"].mean()

    if pd.notna(defensive_avg) and pd.notna(growth_avg) and defensive_avg > growth_avg:
        label = "방어적 섹터 로테이션"
        description = f"방어 섹터 평균({fmt_pct(defensive_avg)})이 성장 섹터 평균({fmt_pct(growth_avg)})보다 높습니다."
    elif pd.notna(growth_avg) and pd.notna(defensive_avg) and growth_avg > defensive_avg:
        label = "성장 섹터 우위"
        description = f"성장 섹터 평균({fmt_pct(growth_avg)})이 방어 섹터 평균({fmt_pct(defensive_avg)})보다 높습니다."
    else:
        label = "섹터 방향성 제한"
        description = "성장·방어 섹터 간 상대강도 차이가 뚜렷하지 않습니다."

    return {
        "label": label,
        "description": description,
        "growth_avg": growth_avg,
        "defensive_avg": defensive_avg,
        "cyclical_avg": cyclical_avg,
    }


def render_sector_rotation_summary(summary: dict):
    st.markdown("### 섹터 로테이션 요약")
    st.metric("섹터 판정", summary["label"])
    st.caption(summary["description"])

    col1, col2, col3 = st.columns(3)
    col1.metric("성장 섹터 평균", fmt_pct(summary.get("growth_avg", np.nan)))
    col2.metric("방어 섹터 평균", fmt_pct(summary.get("defensive_avg", np.nan)))
    col3.metric("경기민감 섹터 평균", fmt_pct(summary.get("cyclical_avg", np.nan)))


def render_data_coverage(df: pd.DataFrame, snap: pd.DataFrame):
    st.markdown("### 데이터 커버리지 및 판정 한계")

    total_assets = snap["asset_name"].nunique()
    total_dates = df["date"].nunique()
    sector_count = snap[snap["asset_type"] == "sector_index"]["asset_name"].nunique()
    country_count = snap[snap["asset_type"] == "equity_index"]["country"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("분석 자산 수", f"{total_assets}개")
    col2.metric("데이터 기간", f"{total_dates}거래일")
    col3.metric("섹터 샘플", f"{sector_count}개")
    col4.metric("국가 지수", f"{country_count}개")

    st.caption(
        "현재 분석은 가격, 변화율, 변동성, 낙폭, 상대강도 기반의 규칙형 분석입니다. "
        "뉴스, 실적 발표, 정책 발언, 기업 이벤트의 원인 분석은 직접 반영하지 않습니다."
    )


def render_sector_summary(sector_df: pd.DataFrame):
    if sector_df.empty:
        st.info("섹터 반응을 표시할 데이터가 부족합니다.")
        return

    strongest = sector_df.sort_values("return_30d", ascending=False).iloc[0]
    weakest = sector_df.sort_values("return_30d", ascending=True).iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("가장 강한 섹터", strongest["sector_display"], fmt_pct(strongest["return_30d"]))
    col2.metric("가장 약한 섹터", weakest["sector_display"], fmt_pct(weakest["return_30d"]))
    col3.metric("상승 섹터 수", f"{int((sector_df['return_30d'] > 0).sum())}개")

    fig = px.bar(
        sector_df.sort_values("return_30d"),
        x="return_30d",
        y="sector_display",
        color="return_30d",
        orientation="h",
        color_continuous_scale=[
            (0.0, "blue"),
            (0.5, "white"),
            (1.0, "red"),
        ],
        color_continuous_midpoint=0,
        labels={"return_30d": "30일 변화율", "sector_display": "섹터"},
        title="미국 섹터 ETF 30일 변화율",
    )
    fig.update_xaxes(tickformat=".1%")
    fig.update_layout(height=430)
    st.plotly_chart(fig, width="stretch")


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


def render_regime_score_history(score_history: pd.DataFrame):
    if score_history.empty:
        st.info("상태 점수 추이를 표시할 데이터가 부족합니다.")
        return

    melted = score_history.melt(
        id_vars=["date"],
        value_vars=["Risk-On", "Risk-Off", "Tightening Stress"],
        var_name="상태",
        value_name="점수",
    )
    melted["상태"] = melted["상태"].map(REGIME_DISPLAY)

    fig = px.line(
        melted,
        x="date",
        y="점수",
        color="상태",
        title="최근 상태 점수 추이",
        labels={"date": "날짜", "점수": "점수"},
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, width="stretch")


# =========================
# App execution
# =========================

def main() -> None:
    df = load_data()
    df = calculate_indicators(df)
    snap = latest_snapshot(df)

    regime, confidence, scores, evidence, rule_checks = classify_regime(snap)
    dominant_signal = build_dominant_signal(evidence)
    insight = generate_insight(regime, dominant_signal)
    score_cards_df = build_score_cards_df(scores)
    notable_assets = get_notable_assets(snap, top_n=5)
    confidence_details = build_confidence_details(scores, confidence)
    overview_metrics = build_overview_metrics(snap)
    country_df = build_country_reaction_df(snap)
    sector_df = build_sector_reaction_df(snap)
    score_history = build_regime_score_history(df, lookback_days=120)
    market_patterns = detect_market_patterns(rule_checks, country_df, sector_df)
    regional_alignment = build_global_regional_alignment(regime, country_df)
    sector_rotation_summary = build_sector_rotation_summary(sector_df)


    latest_date = pd.to_datetime(snap["date"]).max().strftime("%Y-%m-%d")
    display_regime = REGIME_DISPLAY.get(regime, regime)

    st.title("글로벌 시장 상태 진단 대시보드")
    st.caption("글로벌 자산 반응을 기반으로 현재 시장 상태를 분류하고, 주요 변동 신호를 요약합니다.")

    st.markdown(
        """
    이 서비스는 최근 **1년치 내장 글로벌 금융자산 데이터**를 기반으로 현재 시장 상태를 
    **위험 선호 / 위험 회피 / 금리 압박 / 방향성 불명확** 중 하나로 분류합니다.  
    시장 상태 판단은 **최근 30일 반응**을 중심으로 하며, 최근 5일 변화는 단기 경고 신호로 보조 반영합니다.
    """
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "종합 현황",
            "자산 반응 분석",
            "지역·섹터 반응",
            "판정 근거",
            "데이터 조회",
        ]
    )

    with tab1:
        st.subheader("종합 현황")

        col1, col2, col3 = st.columns(3)
        col1.metric("현재 시장 상태", display_regime)
        col2.metric("핵심 신호", dominant_signal)
        col3.metric("분석 범위", "글로벌 기본 데이터")

        st.markdown("### 현재 시장 해석")
        st.info(insight)

        st.markdown("### 대표 요약 수치")
        render_overview_metric_cards(overview_metrics)

        render_market_pattern_cards(market_patterns)

        render_global_regional_alignment(regional_alignment)

        st.markdown("### 주요 이슈 자산")
        st.caption(
            "최근 30일 변화율 또는 120일 기준 이례성 점수를 바탕으로 현재 시장에서 크게 반응한 자산을 선별합니다."
        )
        render_notable_asset_cards(notable_assets)

        st.markdown("### 시장 상태 점수")
        render_regime_score_cards(score_cards_df)

        st.markdown("### 최근 상태 점수 추이")
        render_regime_score_history(score_history)

        st.markdown("### 판정 신뢰도")
        left, right = st.columns([1, 1.4])
        with left:
            render_confidence_gauge(confidence_details)
        with right:
            st.markdown(
                """
    판정 신뢰도는 단순 확률값이 아니라,  
    **최고 점수 상태의 강도**와 **차순위 상태와의 점수 차이**를 바탕으로 계산한 설명용 지표입니다.

    점수 차이가 작거나 최고 점수가 낮으면 시스템은 특정 상태를 과도하게 단정하지 않고  
    **방향성 불명확** 상태로 분류합니다.
    """
            )

        st.caption(f"내장 데이터 기준 최신일: {latest_date}")

    with tab2:
        st.subheader("자산 반응 분석")
        st.markdown(
            """
    자산별 반응을 선택한 지표 기준으로 비교합니다.  
    전체 지표를 한 표에 나열하지 않고, 사용자가 보고 싶은 지표를 선택해 확인하도록 구성했습니다.
    """
        )

        metric_options = {
            "1일 변화율": "return_1d",
            "5일 변화율": "return_5d",
            "30일 변화율": "return_30d",
            "20일 변동성": "volatility_20d",
            "30일 변동성": "volatility_30d",
            "20일 낙폭": "drawdown_20d",
            "60일 낙폭": "drawdown_60d",
            "120일 이례성 점수": "z_score_120d",
        }

        selected_metric_label = st.selectbox(
            "조회 지표 선택",
            list(metric_options.keys()),
            index=2,
        )
        selected_metric = metric_options[selected_metric_label]

        chart_df = snap.dropna(subset=[selected_metric]).copy()
        chart_df["자산유형"] = chart_df["asset_type"].map(localize_asset_type_value)
        chart_df["신호 해석"] = chart_df.apply(label_asset_signal, axis=1)

        fig = px.bar(
            chart_df.sort_values(selected_metric),
            x="asset_name",
            y=selected_metric,
            color="자산유형",
            title=f"자산별 {selected_metric_label}",
            labels={"asset_name": "자산명", selected_metric: selected_metric_label, "자산유형": "자산유형"},
        )
        if selected_metric != "z_score_120d":
            fig.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig, width="stretch")

        st.markdown("### 상위·하위 반응 자산")
        top_col, bottom_col = st.columns(2)

        top_assets = chart_df.sort_values(selected_metric, ascending=False).head(5)
        bottom_assets = chart_df.sort_values(selected_metric, ascending=True).head(5)

        with top_col:
            st.markdown("#### 상위 자산")
            top_display = prepare_display_table(
                top_assets[["asset_name", "asset_type", selected_metric, "신호 해석"]],
                [selected_metric] if selected_metric != "z_score_120d" else [],
            )
            st.dataframe(top_display, width="stretch", hide_index=True)

        with bottom_col:
            st.markdown("#### 하위 자산")
            bottom_display = prepare_display_table(
                bottom_assets[["asset_name", "asset_type", selected_metric, "신호 해석"]],
                [selected_metric] if selected_metric != "z_score_120d" else [],
            )
            st.dataframe(bottom_display, width="stretch", hide_index=True)

        with st.expander("전체 자산 신호 해석 보기"):
            label_df = snap.copy()
            label_df["signal_label"] = label_df.apply(label_asset_signal, axis=1)
            label_df["market_meaning"] = label_df.apply(market_meaning_from_signal, axis=1)

            label_df = label_df[
                [
                    "asset_name",
                    "asset_type",
                    "return_1d",
                    "return_5d",
                    "return_30d",
                    "volatility_30d",
                    "drawdown_60d",
                    "z_score_120d",
                    "signal_label",
                    "market_meaning",
                ]
            ]

            label_display = prepare_display_table(
                label_df,
                ["return_1d", "return_5d", "return_30d", "volatility_30d", "drawdown_60d"],
            )
            st.dataframe(label_display, width="stretch", hide_index=True)

    with tab3:
        st.subheader("지역·섹터 반응")
        st.markdown(
            """
    국가별 대표 지수와 미국 섹터 ETF 반응을 분리해서 보여줍니다.  
    국가 수가 많지 않은 현재 구조에서는 지도보다 카드형 반응 보드와 순위 차트가 더 직관적입니다.
    """
        )

        st.markdown("## 국가별 시장 반응")
        render_country_cards(country_df)
        render_country_ranking(country_df)

        st.divider()

        st.markdown("## 미국 섹터 ETF 반응")
        st.caption("섹터 데이터는 기본 데모용 미국 섹터 ETF 샘플입니다. 다른 국가·테마·종목 데이터는 사용자 업로드로 확장하는 구조를 전제로 합니다.")

        render_sector_rotation_summary(sector_rotation_summary)
        render_sector_summary(sector_df)

    with tab4:
        st.subheader("판정 근거")
        st.markdown(
            """
    시장 상태는 단일 자산 하나로 판단하지 않고, 여러 자산군의 반응 조합으로 판정합니다.  
    각 상태별 조건이 충족될 때 점수를 부여하고, 점수 차이가 작거나 최고 점수가 낮으면 **방향성 불명확**으로 분류합니다.
    """
        )

        st.markdown("### 상태별 판정 기준")
        st.caption(
            "각 카드에는 해당 시장 상태의 점수와 판정 기준별 충족 여부를 표시합니다. "
            "충족된 기준은 ✅, 충족되지 않은 기준은 ❌로 표시합니다."
        )

        render_regime_rule_cards(rule_checks, scores)

    with tab5:
        st.subheader("데이터 조회")
        st.markdown(
            """
    계산된 지표를 확인하기 위한 상세 조회 탭입니다.  
    대표 화면에서는 결론과 핵심 신호를 먼저 보여주고, 세부 계산 결과는 이곳에서 확인합니다.
    """
        )

        snapshot_display = snap[
            [
                "date",
                "asset_name",
                "asset_type",
                "country",
                "sector",
                "value",
                "return_1d",
                "return_5d",
                "return_30d",
                "volatility_20d",
                "volatility_30d",
                "drawdown_20d",
                "drawdown_60d",
                "z_score_120d",
                "change_5d",
                "change_30d",
            ]
        ]

        snapshot_display = prepare_display_table(
            snapshot_display,
            ["return_1d", "return_5d", "return_30d", "volatility_20d", "volatility_30d", "drawdown_20d", "drawdown_60d"],
        )

        st.dataframe(snapshot_display, width="stretch", hide_index=True)

        render_data_coverage(df, snap)

        st.warning(
            "본 대시보드는 투자 추천이 아니라, 입력 데이터 기반 시장 상태 해석을 제공하는 분석 도구입니다. "
            "매수·매도 판단이나 수익 예측을 목적으로 사용하지 않습니다."
        )


if __name__ == "__main__":
    main()
