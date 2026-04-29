from pathlib import Path

import streamlit as st


def setup_page_config() -> None:
    st.set_page_config(
        page_title="글로벌 시장 상태 진단 대시보드",
        layout="wide",
    )


DATA_DIR = Path("data")
DATA_PATH = DATA_DIR / "default_market_indicators.csv"

ASSETS = [
    {"asset_name": "S&P500", "asset_type": "equity_index", "start": 5000, "country": "USA", "sector": "broad_market"},
    {"asset_name": "Nasdaq", "asset_type": "equity_index", "start": 16000, "country": "USA", "sector": "tech_growth"},
    {"asset_name": "KOSPI", "asset_type": "equity_index", "start": 2700, "country": "Korea", "sector": "broad_market"},
    {"asset_name": "Nikkei225", "asset_type": "equity_index", "start": 39000, "country": "Japan", "sector": "broad_market"},
    {"asset_name": "DAX", "asset_type": "equity_index", "start": 18000, "country": "Germany", "sector": "broad_market"},
    {"asset_name": "FTSE100", "asset_type": "equity_index", "start": 7900, "country": "UK", "sector": "broad_market"},
    {"asset_name": "HangSeng", "asset_type": "equity_index", "start": 17000, "country": "Hong Kong", "sector": "broad_market"},
    {"asset_name": "Nifty50", "asset_type": "equity_index", "start": 22000, "country": "India", "sector": "broad_market"},
    {"asset_name": "Gold", "asset_type": "safe_asset", "start": 2300, "country": "Global", "sector": "precious_metal"},
    {"asset_name": "US10Y", "asset_type": "bond_yield", "start": 4.3, "country": "USA", "sector": "rate"},
    {"asset_name": "VIX", "asset_type": "volatility_index", "start": 18, "country": "USA", "sector": "volatility"},
    {"asset_name": "USD/KRW", "asset_type": "fx", "start": 1350, "country": "Korea", "sector": "fx"},
    {"asset_name": "BTC", "asset_type": "crypto", "start": 65000, "country": "Global", "sector": "crypto"},
    {"asset_name": "Oil", "asset_type": "commodity", "start": 78, "country": "Global", "sector": "energy"},
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
