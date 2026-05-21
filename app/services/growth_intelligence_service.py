from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


@dataclass(frozen=True)
class ChannelMetric:
    source: str
    revenue: float
    spend: float
    leads: int
    sales: int
    visitors: int
    conversion_rate: float
    previous_revenue: float = 0

    @property
    def roi(self) -> float:
        if self.spend <= 0:
            return 0
        return (self.revenue - self.spend) / self.spend

    @property
    def roas(self) -> float:
        if self.spend <= 0:
            return 0
        return self.revenue / self.spend

    @property
    def cpl(self) -> float:
        if self.leads <= 0:
            return 0
        return self.spend / self.leads


@dataclass(frozen=True)
class Insight:
    title: str
    explanation: str
    severity: Severity
    confidence: float
    evidence: str


@dataclass(frozen=True)
class ActionItem:
    title: str
    why: str
    expected_effect: str
    revenue_impact: float
    complexity: str
    time_to_execute: str
    priority: int


@dataclass(frozen=True)
class Forecast:
    metric: str
    current: float
    predicted: float
    lower_bound: float
    upper_bound: float
    horizon_days: int
    explanation: str


def build_profit_map(metrics: list[ChannelMetric]) -> dict:
    total_revenue = sum(item.revenue for item in metrics) or 1
    nodes = []
    for item in sorted(metrics, key=lambda metric: metric.revenue, reverse=True):
        nodes.append(
            {
                "source": item.source,
                "size": round(item.revenue, 2),
                "leads": item.leads,
                "sales": item.sales,
                "roi": round(item.roi, 2),
                "roas": round(item.roas, 2),
                "conversion_rate": round(item.conversion_rate, 4),
                "share": round(item.revenue / total_revenue, 4),
                "status": channel_status(item),
            }
        )
    return {"total_revenue": round(total_revenue, 2), "nodes": nodes}


def channel_status(metric: ChannelMetric) -> str:
    if metric.roi >= 1 and metric.conversion_rate >= 0.04:
        return "масштабировать"
    if metric.roi < 0 and metric.spend > 0:
        return "теряет деньги"
    if metric.leads > 0 and metric.sales == 0:
        return "проверить качество лидов"
    return "наблюдать"


def detect_insights(metrics: list[ChannelMetric]) -> list[Insight]:
    insights: list[Insight] = []
    if not metrics:
        return [
            Insight(
                title="Недостаточно данных",
                explanation="Подключите аналитику, CRM или скрипт отслеживания, чтобы система могла найти потери и точки роста.",
                severity=Severity.medium,
                confidence=0.9,
                evidence="Нет нормализованных метрик каналов.",
            )
        ]

    best = max(metrics, key=lambda item: item.revenue)
    worst_roi = min(metrics, key=lambda item: item.roi)

    insights.append(
        Insight(
            title=f"Больше всего денег приносит {best.source}",
            explanation=f"Источник дает {best.revenue:.0f} дохода и {best.leads} лидов. Его стоит проверить на возможность масштабирования.",
            severity=Severity.low,
            confidence=0.78,
            evidence=f"ROAS {best.roas:.2f}, ROI {best.roi:.2f}, конверсия {best.conversion_rate:.1%}.",
        )
    )

    if worst_roi.spend > 0 and worst_roi.roi < 0:
        insights.append(
            Insight(
                title=f"{worst_roi.source} теряет бюджет",
                explanation="Канал тратит деньги, но не возвращает достаточно дохода. Нужно проверить аудиторию, оффер и посадочную страницу.",
                severity=Severity.high,
                confidence=0.82,
                evidence=f"Расход {worst_roi.spend:.0f}, доход {worst_roi.revenue:.0f}, ROI {worst_roi.roi:.2f}.",
            )
        )

    for item in metrics:
        if item.previous_revenue > 0:
            drop = (item.previous_revenue - item.revenue) / item.previous_revenue
            if drop >= 0.25:
                insights.append(
                    Insight(
                        title=f"Падение дохода из {item.source}",
                        explanation="Источник резко просел относительно прошлого периода. Нужно проверить кампании, трекинг, сайт и конкурентов.",
                        severity=Severity.critical if drop >= 0.45 else Severity.high,
                        confidence=0.76,
                        evidence=f"Падение на {drop:.0%}: было {item.previous_revenue:.0f}, стало {item.revenue:.0f}.",
                    )
                )
    return insights


def generate_today_actions(metrics: list[ChannelMetric]) -> list[ActionItem]:
    actions: list[ActionItem] = []
    for item in metrics:
        if item.roi < 0 and item.spend > 0:
            actions.append(
                ActionItem(
                    title=f"Остановить потери в {item.source}",
                    why="Канал тратит бюджет и возвращает меньше денег, чем вложено.",
                    expected_effect="Снижение лишних расходов и рост общей рентабельности.",
                    revenue_impact=abs(item.revenue - item.spend),
                    complexity="средняя",
                    time_to_execute="30-60 минут",
                    priority=95,
                )
            )
        if item.leads > 0 and item.sales == 0:
            actions.append(
                ActionItem(
                    title=f"Проверить качество лидов из {item.source}",
                    why="Лиды есть, продаж нет. Вероятна проблема в оффере, форме, менеджере или CRM-этапе.",
                    expected_effect="Повышение конверсии из лида в продажу.",
                    revenue_impact=max(item.leads * 500, 1000),
                    complexity="средняя",
                    time_to_execute="1-2 часа",
                    priority=82,
                )
            )
    best = max(metrics, key=lambda item: item.roi, default=None)
    if best and best.roi > 1:
        actions.append(
            ActionItem(
                title=f"Масштабировать {best.source}",
                why="Канал показывает высокую окупаемость и может дать больше лидов при увеличении бюджета.",
                expected_effect="Рост лидов и дохода без смены стратегии.",
                revenue_impact=best.revenue * 0.2,
                complexity="низкая",
                time_to_execute="20 минут",
                priority=75,
            )
        )
    return sorted(actions, key=lambda item: item.priority, reverse=True)


def forecast_revenue(metrics: list[ChannelMetric], horizon_days: int = 30) -> Forecast:
    current = sum(item.revenue for item in metrics)
    weighted_growth = 0.0
    active = 0
    for item in metrics:
        if item.previous_revenue > 0:
            weighted_growth += (item.revenue - item.previous_revenue) / item.previous_revenue
            active += 1
    avg_growth = weighted_growth / active if active else 0.08
    predicted = current * (1 + avg_growth)
    spread = max(abs(avg_growth), 0.08)
    return Forecast(
        metric="доход",
        current=round(current, 2),
        predicted=round(predicted, 2),
        lower_bound=round(predicted * (1 - spread), 2),
        upper_bound=round(predicted * (1 + spread), 2),
        horizon_days=horizon_days,
        explanation="Прогноз основан на динамике дохода по каналам и текущей окупаемости.",
    )


def demo_metrics() -> list[ChannelMetric]:
    return [
        ChannelMetric("TikTok Ads", revenue=182000, spend=54000, leads=96, sales=18, visitors=4200, conversion_rate=0.043, previous_revenue=145000),
        ChannelMetric("Instagram", revenue=76000, spend=68000, leads=104, sales=7, visitors=6100, conversion_rate=0.017, previous_revenue=91000),
        ChannelMetric("Поиск", revenue=138000, spend=22000, leads=64, sales=14, visitors=3100, conversion_rate=0.036, previous_revenue=132000),
        ChannelMetric("Партнерский блог", revenue=94000, spend=9000, leads=28, sales=9, visitors=860, conversion_rate=0.061, previous_revenue=52000),
        ChannelMetric("Email", revenue=42000, spend=6000, leads=21, sales=5, visitors=740, conversion_rate=0.049, previous_revenue=48000),
    ]
