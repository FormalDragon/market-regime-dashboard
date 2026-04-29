import pandas as pd

from src.display_utils import fmt_pct, relative_strength_label


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
