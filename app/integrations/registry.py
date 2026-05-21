from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationSpec:
    code: str
    title: str
    category: str
    purpose: str
    auth_type: str


INTEGRATIONS = [
    IntegrationSpec("ga4", "Google Analytics 4", "analytics", "Источники, события, аудитории и конверсии.", "oauth2"),
    IntegrationSpec("gsc", "Google Search Console", "analytics", "Запросы, показы, клики, CTR и позиции.", "oauth2"),
    IntegrationSpec("yandex_metrika", "Яндекс Метрика", "analytics", "Визиты, цели, источники и поведение.", "oauth2"),
    IntegrationSpec("google_ads", "Google Ads", "ads", "Кампании, расходы, клики, конверсии и ROAS.", "oauth2"),
    IntegrationSpec("meta_ads", "Meta Ads", "ads", "Instagram/Facebook реклама, CPL и креативы.", "oauth2"),
    IntegrationSpec("tiktok_ads", "TikTok Ads", "ads", "Видео, клики, лиды и эффективность кампаний.", "oauth2"),
    IntegrationSpec("hubspot", "HubSpot", "crm", "Лиды, сделки, стадии и revenue attribution.", "oauth2"),
    IntegrationSpec("bitrix", "Bitrix24", "crm", "Лиды, сделки, источники и менеджеры.", "oauth2"),
    IntegrationSpec("amocrm", "AmoCRM", "crm", "Воронки, сделки и причины потерь.", "oauth2"),
    IntegrationSpec("mailchimp", "Mailchimp", "email", "Email-кампании, аудитории и конверсии.", "api_key"),
    IntegrationSpec("klaviyo", "Klaviyo", "email", "Email/SMS кампании и revenue attribution.", "api_key"),
]


def grouped_integrations() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in INTEGRATIONS:
        grouped.setdefault(item.category, []).append(item.__dict__)
    return grouped
