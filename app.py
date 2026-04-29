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

import pandas as pd
import streamlit as st

from src.config import REGIME_DISPLAY, setup_page_config
from src.data_loader import load_data
from src.display_utils import get_notable_assets, prepare_display_table
from src.indicators import build_regime_score_history, calculate_indicators, latest_snapshot
from src.patterns import detect_market_patterns
from src.regime_rules import (
    build_confidence_details,
    build_dominant_signal,
    build_score_cards_df,
    classify_regime,
    generate_insight,
)
from src.ui_sections import (
    build_country_reaction_df,
    build_global_regional_alignment,
    build_overview_metrics,
    build_sector_reaction_df,
    build_sector_rotation_summary,
    render_asset_reaction_analysis_tab,
    render_confidence_gauge,
    render_country_cards,
    render_country_ranking,
    render_data_coverage,
    render_global_regional_alignment,
    render_overview_tab_sections,
    render_regime_rule_cards,
    render_sector_rotation_summary,
    render_sector_summary,
)


def main() -> None:
    setup_page_config()

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "종합 현황",
        "자산 반응 분석",
        "지역·섹터 반응",
        "판정 근거",
        "데이터 조회",
    ])

    with tab1:
        st.subheader("종합 현황")
        render_overview_tab_sections(
            display_regime=display_regime,
            dominant_signal=dominant_signal,
            insight=insight,
            market_patterns=market_patterns,
            overview_metrics=overview_metrics,
            notable_assets=notable_assets,
            score_cards_df=score_cards_df,
            score_history=score_history,
            regime_display=REGIME_DISPLAY,
        )

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
        render_asset_reaction_analysis_tab(snap)

    with tab3:
        st.subheader("지역·섹터 반응")
        st.markdown(
            """
    국가별 대표 지수와 미국 섹터 ETF 반응을 분리해서 보여줍니다.
    국가 수가 많지 않은 현재 구조에서는 지도보다 카드형 반응 보드와 순위 차트가 더 직관적입니다.
    """
        )
        render_global_regional_alignment(regional_alignment)

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
        st.caption("각 카드에는 해당 시장 상태의 점수와 판정 기준별 충족 여부를 표시합니다. 충족된 기준은 ✅, 충족되지 않은 기준은 ❌로 표시합니다.")
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
                "date", "asset_name", "asset_type", "country", "sector", "value", "return_1d", "return_5d", "return_30d",
                "volatility_20d", "volatility_30d", "drawdown_20d", "drawdown_60d", "z_score_120d", "change_5d", "change_30d",
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
