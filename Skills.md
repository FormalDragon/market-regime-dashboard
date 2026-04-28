# Skills.md - Global Market Regime Dashboard

## Purpose
내장 글로벌 금융시장 데이터를 기반으로 현재 글로벌 시장 상태를 진단하고, 사용자 업로드 데이터는 국가·섹터·자산 반응 레이어로 결합해 해석한다.

## Input Data
기본 내부 스키마:
date, asset_name, asset_type, value, country, sector

## Asset Types
- equity_index: S&P500, Nasdaq, KOSPI 등 주가지수
- safe_asset: Gold
- bond_yield: US10Y
- volatility_index: VIX
- fx: USD/KRW
- crypto: BTC
- commodity: Oil

## Built-in Assets
- S&P500
- Nasdaq
- KOSPI
- Nikkei225
- DAX
- FTSE100
- HangSeng
- Nifty50
- Gold
- US10Y
- VIX
- USD/KRW
- BTC
- Oil

## Indicators
- return_1d
- return_5d
- volatility_20d
- drawdown_20d

bond_yield는 수익률이 아니라 변화폭으로 계산한다.
VIX는 변화율로 계산한다.

## Market Regimes
- Risk-On
- Risk-Off
- Tightening Stress
- Mixed / Uncertain

## Classification
상태별 점수 기반으로 분류한다.
Risk-On은 주식 상승, BTC 상승, VIX 하락, Gold 약세, USD/KRW 하락을 근거로 한다.
Risk-Off는 주식 하락, BTC 하락, VIX 상승, Gold 상대강세, USD/KRW 상승을 근거로 한다.
Tightening Stress는 US10Y 상승, Nasdaq 약세, USD/KRW 상승, BTC 약세를 근거로 한다.
점수 차이가 작거나 최고 점수가 낮으면 Mixed / Uncertain으로 분류한다.

## Visualization
Streamlit 화면은 다음 탭으로 구성한다.
1. Global Summary
2. Cross-Asset Reaction
3. Regional Map
4. Regime Score
5. Auto Insight

지도는 국가별 equity_index의 5일 수익률을 표시한다.
국가 선택은 지도 클릭이 아니라 selectbox로 구현한다.

## Insight
투자 추천이 아니라 시장 상태 해석 문장만 생성한다.
매수/매도 권고 표현은 사용하지 않는다.