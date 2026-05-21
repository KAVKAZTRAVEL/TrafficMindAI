from app.models import TrafficSource
from app.services.quality_score_service import quality_label


def explain_sources(sources: list[TrafficSource]) -> str:
    if not sources:
        return "Пока мало данных. Установите AI Tracking Script или подключите GA4, и я покажу лучшие источники."
    best = max(sources, key=lambda item: item.quality_score)
    weak = min(sources, key=lambda item: item.quality_score)
    return (
        f"Лучший источник сейчас: {best.source_domain}. Качество {best.quality_score}/100 "
        f"({quality_label(best.quality_score)}). Слабое место: {weak.source_domain}, "
        f"там качество {weak.quality_score}/100. Проверьте страницу входа и призыв к действию для этого канала."
    )


def recommendations_from_audit(audit: dict) -> list[str]:
    items = []
    if not audit.get("analytics"):
        items.append("Подключите GA4 или AI Tracking Script, чтобы видеть реальные источники и заявки.")
    if not audit.get("lead_forms"):
        items.append("Добавьте короткую форму заявки или заметную кнопку связи выше первого экрана.")
    if len(audit.get("seo", [])) < 2:
        items.append("Заполните title и meta description: это поможет поиску и понятности страницы.")
    if not items:
        items.append("Критичных проблем не видно. Следующий шаг: собрать трафик и найти слабые источники.")
    return items
