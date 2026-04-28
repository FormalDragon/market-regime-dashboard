import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COUNTRY_FLAG, MAX_SCORES, REGIME_MEANINGS, REGIME_WITH_EN
from src.display_utils import (
    fmt_num,
    fmt_pct,
    label_asset_signal,
    localize_asset_type_value,
    localize_country_value,
    localize_sector_value,
    market_meaning_from_signal,
    prepare_display_table,
)


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


def render_market_pattern_cards(patterns: list[dict]):
    st.markdown("### 감지된 시장 패턴")
    st.caption("사전에 정의한 규칙 조합을 기준으로, 현재 관찰되는 시장 패턴을 표시합니다.")

    cols = st.columns(min(3, len(patterns)))

    for idx, pattern in enumerate(patterns):
        with cols[idx % len(cols)]:
            st.markdown(f"#### {pattern['name']}")
            st.metric("패턴 강도", pattern["strength"])
            st.caption(pattern["basis"])


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

    return {"label": label, "description": description}


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
        [equity["return_30d"] > threshold, equity["return_30d"] < -threshold],
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
        color_continuous_scale=[(0.0, "blue"), (0.5, "white"), (1.0, "red")],
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
        return {"label": "판정 제한", "description": "섹터 데이터가 부족합니다."}

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
        color_continuous_scale=[(0.0, "blue"), (0.5, "white"), (1.0, "red")],
        color_continuous_midpoint=0,
        labels={"return_30d": "30일 변화율", "sector_display": "섹터"},
        title="미국 섹터 ETF 30일 변화율",
    )
    fig.update_xaxes(tickformat=".1%")
    fig.update_layout(height=430)
    st.plotly_chart(fig, width="stretch")


def render_regime_score_history(score_history: pd.DataFrame, regime_display: dict[str, str]):
    if score_history.empty:
        st.info("상태 점수 추이를 표시할 데이터가 부족합니다.")
        return

    melted = score_history.melt(
        id_vars=["date"],
        value_vars=["Risk-On", "Risk-Off", "Tightening Stress"],
        var_name="상태",
        value_name="점수",
    )
    melted["상태"] = melted["상태"].map(regime_display)

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


def render_asset_reaction_analysis_tab(snap: pd.DataFrame):
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

    selected_metric_label = st.selectbox("조회 지표 선택", list(metric_options.keys()), index=2)
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
                "asset_name", "asset_type", "return_1d", "return_5d", "return_30d", "volatility_30d", "drawdown_60d", "z_score_120d", "signal_label", "market_meaning",
            ]
        ]

        label_display = prepare_display_table(
            label_df,
            ["return_1d", "return_5d", "return_30d", "volatility_30d", "drawdown_60d"],
        )
        st.dataframe(label_display, width="stretch", hide_index=True)
