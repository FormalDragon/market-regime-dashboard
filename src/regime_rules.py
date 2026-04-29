import pandas as pd

from src.config import MAX_SCORES, REGIME_DISPLAY, REGIME_MEANINGS, REGIME_WITH_EN
from src.display_utils import classify_signal_strength, relative_strength_label, score_from_strength


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

    if sp is not None and pd.notna(sp["return_30d"]):
        add_rule("Risk-On", "S&P500 30일 변화율 상승", sp["return_30d"] > 0, classify_signal_strength("equity_index", sp["return_30d"]))

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule("Risk-On", "Nasdaq 30일 변화율 상승", nasdaq["return_30d"] > 0, classify_signal_strength("equity_index", nasdaq["return_30d"]))

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule("Risk-On", "BTC 30일 변화율 상승", btc["return_30d"] > 0, classify_signal_strength("crypto", btc["return_30d"]))

    if vix is not None and pd.notna(vix["return_30d"]):
        add_rule("Risk-On", "VIX 30일 변화율 하락", vix["return_30d"] < 0, classify_signal_strength("volatility_index", vix["return_30d"]))

    if gold is not None and sp is not None and pd.notna(gold["return_30d"]) and pd.notna(sp["return_30d"]):
        diff = sp["return_30d"] - gold["return_30d"]
        add_rule("Risk-On", "Gold가 S&P500 대비 30일 상대약세", gold["return_30d"] < sp["return_30d"], relative_strength_label(diff))

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule("Risk-On", "USD/KRW 30일 변화율 하락", usdkrw["return_30d"] < 0, classify_signal_strength("fx", usdkrw["return_30d"]))

    if xlk is not None and xlu is not None and pd.notna(xlk["return_30d"]) and pd.notna(xlu["return_30d"]):
        diff = xlk["return_30d"] - xlu["return_30d"]
        add_rule("Risk-On", "기술 섹터가 방어 섹터 대비 강세", xlk["return_30d"] > xlu["return_30d"], relative_strength_label(diff))

    if sp is not None and pd.notna(sp["return_5d"]):
        add_rule("Risk-On", "S&P500 5일 변화율 +2% 이상 단기 강세", sp["return_5d"] > 0.02, classify_signal_strength("equity_index", sp["return_5d"]))

    if sp is not None and pd.notna(sp["return_30d"]):
        add_rule("Risk-Off", "S&P500 30일 변화율 하락", sp["return_30d"] < 0, classify_signal_strength("equity_index", sp["return_30d"]))

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule("Risk-Off", "Nasdaq 30일 변화율 하락", nasdaq["return_30d"] < 0, classify_signal_strength("equity_index", nasdaq["return_30d"]))

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule("Risk-Off", "BTC 30일 변화율 하락", btc["return_30d"] < 0, classify_signal_strength("crypto", btc["return_30d"]))

    if vix is not None and pd.notna(vix["return_30d"]):
        add_rule("Risk-Off", "VIX 30일 변화율 상승", vix["return_30d"] > 0, classify_signal_strength("volatility_index", vix["return_30d"]))

    if gold is not None and sp is not None and pd.notna(gold["return_30d"]) and pd.notna(sp["return_30d"]):
        diff = gold["return_30d"] - sp["return_30d"]
        add_rule("Risk-Off", "Gold가 S&P500 대비 30일 상대강세", gold["return_30d"] > sp["return_30d"], relative_strength_label(diff))

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule("Risk-Off", "USD/KRW 30일 변화율 상승", usdkrw["return_30d"] > 0, classify_signal_strength("fx", usdkrw["return_30d"]))

    if xlk is not None and xlu is not None and pd.notna(xlk["return_30d"]) and pd.notna(xlu["return_30d"]):
        diff = xlu["return_30d"] - xlk["return_30d"]
        add_rule("Risk-Off", "방어 섹터가 기술 섹터 대비 강세", xlu["return_30d"] > xlk["return_30d"], relative_strength_label(diff))

    if sp is not None and pd.notna(sp["return_5d"]):
        add_rule("Risk-Off", "S&P500 5일 변화율 -2% 이하 단기 급락", sp["return_5d"] < -0.02, classify_signal_strength("equity_index", sp["return_5d"]))

    if us10y is not None and pd.notna(us10y["change_30d"]):
        add_rule("Tightening Stress", "US10Y 금리 30일 변화폭 상승", us10y["change_30d"] > 0, classify_signal_strength("bond_yield", us10y["change_30d"], metric_type="yield_change"))

    if nasdaq is not None and pd.notna(nasdaq["return_30d"]):
        add_rule("Tightening Stress", "Nasdaq 30일 변화율 하락", nasdaq["return_30d"] < 0, classify_signal_strength("equity_index", nasdaq["return_30d"]))

    if usdkrw is not None and pd.notna(usdkrw["return_30d"]):
        add_rule("Tightening Stress", "USD/KRW 30일 변화율 상승", usdkrw["return_30d"] > 0, classify_signal_strength("fx", usdkrw["return_30d"]))

    if btc is not None and pd.notna(btc["return_30d"]):
        add_rule("Tightening Stress", "BTC 30일 변화율 하락", btc["return_30d"] < 0, classify_signal_strength("crypto", btc["return_30d"]))

    if xlk is not None and pd.notna(xlk["return_30d"]):
        add_rule("Tightening Stress", "기술 섹터 30일 약세", xlk["return_30d"] < 0, classify_signal_strength("sector_index", xlk["return_30d"]))

    if xlp is not None and xlk is not None and pd.notna(xlp["return_30d"]) and pd.notna(xlk["return_30d"]):
        diff = xlp["return_30d"] - xlk["return_30d"]
        add_rule("Tightening Stress", "필수소비재가 기술 섹터 대비 강세", xlp["return_30d"] > xlk["return_30d"], relative_strength_label(diff))

    if us10y is not None and pd.notna(us10y["change_5d"]):
        add_rule("Tightening Stress", "US10Y 금리 5일 변화폭 상승", us10y["change_5d"] > 0, classify_signal_strength("bond_yield", us10y["change_5d"], metric_type="yield_change"))

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_regime, top_score = sorted_scores[0]
    _, second_score = sorted_scores[1]
    score_gap = top_score - second_score

    regime = "Mixed / Uncertain" if top_score <= 4 or score_gap <= 1 else top_regime
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
        return f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. 핵심 신호는 **{dominant_signal}**입니다. 최근 30일 기준 위험자산 약세와 방어적 신호가 함께 관찰되며, 시장 참여자의 위험 회피 성향이 강화된 구간으로 해석됩니다."

    if regime == "Risk-On":
        return f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. 핵심 신호는 **{dominant_signal}**입니다. 최근 30일 기준 위험자산 선호와 변동성 완화 신호가 관찰되며, 시장 참여자의 위험 감수 성향이 강화된 구간으로 해석됩니다."

    if regime == "Tightening Stress":
        return f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. 핵심 신호는 **{dominant_signal}**입니다. 최근 30일 기준 금리 상승, 달러 강세, 성장주 약세가 함께 나타나는지 확인할 필요가 있습니다. 이는 유동성 부담이 시장에 반영되는 구간으로 해석됩니다."

    return f"현재 글로벌 시장은 **{display_regime}** 상태로 분류됩니다. 핵심 신호는 **{dominant_signal}**입니다. 최근 30일 기준 주요 자산군 간 신호가 엇갈리거나 상태 점수 차이가 충분하지 않습니다. 따라서 특정 방향으로 단정하기보다 방향성이 불명확한 구간으로 해석합니다."


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
