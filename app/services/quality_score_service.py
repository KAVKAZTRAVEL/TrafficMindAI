def clamp(value: float, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(round(value))))


def calculate_quality_score(
    avg_time: float,
    pages_per_session: float,
    clicks: int,
    forms: int,
    scroll_depth: float,
    returns: int,
    bounce_rate: float,
    conversions: int,
) -> int:
    score = 0
    score += min(avg_time / 180, 1) * 18
    score += min(pages_per_session / 4, 1) * 16
    score += min(clicks / 20, 1) * 12
    score += min(forms / 5, 1) * 16
    score += min(scroll_depth / 80, 1) * 12
    score += min(returns / 10, 1) * 8
    score += (1 - min(bounce_rate, 1)) * 10
    score += min(conversions / 5, 1) * 8
    return clamp(score)


def quality_label(score: int) -> str:
    if score >= 70:
        return "Высокое качество"
    if score >= 40:
        return "Среднее качество"
    return "Низкое качество"
