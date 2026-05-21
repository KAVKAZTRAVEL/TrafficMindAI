from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class IntegrationSpec:
    code: str
    title: str
    category: str
    purpose: str
    auth_type: str
    setup_time: str
    env_prefix: str
    scopes: tuple[str, ...] = ()
    auth_url: str | None = None
    docs_url: str | None = None
    user_fields: tuple[str, ...] = ()
    install_steps: tuple[str, ...] = ()


CATEGORY_TITLES = {
    "analytics": "Аналитика",
    "ads": "Реклама",
    "crm": "CRM",
    "social": "Соцсети",
    "email": "Email",
    "pixels": "Пиксели и теги",
    "calls": "Call Tracking",
}


INTEGRATIONS = [
    IntegrationSpec(
        "ga4",
        "Google Analytics 4",
        "analytics",
        "Источники, события, аудитории, конверсии и путь пользователя.",
        "oauth2",
        "2 минуты",
        "GOOGLE",
        scopes=("https://www.googleapis.com/auth/analytics.readonly",),
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        docs_url="https://developers.google.com/analytics/devguides/reporting/data/v1",
    ),
    IntegrationSpec(
        "gsc",
        "Google Search Console",
        "analytics",
        "Запросы, показы, клики, CTR, позиции и SEO-возможности.",
        "oauth2",
        "2 минуты",
        "GOOGLE",
        scopes=("https://www.googleapis.com/auth/webmasters.readonly",),
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        docs_url="https://developers.google.com/webmaster-tools",
    ),
    IntegrationSpec(
        "yandex_metrika",
        "Яндекс Метрика",
        "analytics",
        "Визиты, цели, источники, поведение и конверсии.",
        "oauth2",
        "2 минуты",
        "YANDEX",
        auth_url="https://oauth.yandex.ru/authorize",
        docs_url="https://yandex.ru/dev/metrika/",
    ),
    IntegrationSpec("google_ads", "Google Ads", "ads", "Расходы, кампании, клики, конверсии, CPL, ROAS.", "oauth2", "3 минуты", "GOOGLE", scopes=("https://www.googleapis.com/auth/adwords",), auth_url="https://accounts.google.com/o/oauth2/v2/auth", docs_url="https://developers.google.com/google-ads/api/docs/start"),
    IntegrationSpec("meta_ads", "Meta Ads", "ads", "Instagram/Facebook реклама, креативы, расходы, CPL и лиды.", "oauth2", "3 минуты", "META", scopes=("ads_read", "business_management", "pages_read_engagement"), auth_url="https://www.facebook.com/v20.0/dialog/oauth", docs_url="https://developers.facebook.com/docs/marketing-apis/"),
    IntegrationSpec("tiktok_ads", "TikTok Ads", "ads", "Кампании, видео, расходы, лиды и эффективность креативов.", "oauth2", "3 минуты", "TIKTOK", scopes=("advertiser.read", "report.read"), auth_url="https://business-api.tiktok.com/portal/auth", docs_url="https://business-api.tiktok.com/portal/docs"),
    IntegrationSpec("linkedin_ads", "LinkedIn Ads", "ads", "B2B кампании, расходы, лиды и CPL.", "oauth2", "3 минуты", "LINKEDIN", scopes=("r_ads_reporting", "r_ads"), auth_url="https://www.linkedin.com/oauth/v2/authorization", docs_url="https://learn.microsoft.com/en-us/linkedin/marketing/"),
    IntegrationSpec("hubspot", "HubSpot", "crm", "Лиды, сделки, стадии, источники и revenue attribution.", "oauth2", "2 минуты", "HUBSPOT", scopes=("crm.objects.contacts.read", "crm.objects.deals.read"), auth_url="https://app.hubspot.com/oauth/authorize", docs_url="https://developers.hubspot.com/docs/api/overview"),
    IntegrationSpec("bitrix24", "Bitrix24", "crm", "Лиды, сделки, статусы, менеджеры и причины потерь.", "oauth2", "3 минуты", "BITRIX24", auth_url="https://oauth.bitrix.info/oauth/authorize/", docs_url="https://training.bitrix24.com/rest_help/", user_fields=("Домен портала, например example.bitrix24.ru",)),
    IntegrationSpec("amocrm", "AmoCRM", "crm", "Воронки, сделки, источники, этапы и причины потерь.", "oauth2", "3 минуты", "AMOCRM", auth_url="https://www.amocrm.ru/oauth", docs_url="https://www.amocrm.ru/developers/content/oauth/step-by-step", user_fields=("Поддомен AmoCRM, например company.amocrm.ru",)),
    IntegrationSpec("instagram", "Instagram", "social", "Публикации, охваты, вовлеченность и контент, который приводит лиды.", "oauth2", "3 минуты", "META", scopes=("instagram_basic", "instagram_manage_insights", "pages_show_list"), auth_url="https://www.facebook.com/v20.0/dialog/oauth", docs_url="https://developers.facebook.com/docs/instagram-platform/"),
    IntegrationSpec("tiktok", "TikTok", "social", "Видео, просмотры, вовлеченность, идеи Reels и контентные тренды.", "oauth2", "3 минуты", "TIKTOK", scopes=("user.info.basic", "video.list"), auth_url="https://www.tiktok.com/v2/auth/authorize/", docs_url="https://developers.tiktok.com/doc/overview/"),
    IntegrationSpec("facebook", "Facebook", "social", "Страницы, посты, охваты, вовлеченность и переходы.", "oauth2", "3 минуты", "META", scopes=("pages_read_engagement", "pages_read_user_content"), auth_url="https://www.facebook.com/v20.0/dialog/oauth", docs_url="https://developers.facebook.com/docs/pages-api/"),
    IntegrationSpec("linkedin", "LinkedIn", "social", "B2B публикации, вовлеченность и контентные сигналы.", "oauth2", "3 минуты", "LINKEDIN", scopes=("openid", "profile", "w_member_social"), auth_url="https://www.linkedin.com/oauth/v2/authorization", docs_url="https://learn.microsoft.com/en-us/linkedin/"),
    IntegrationSpec("youtube", "YouTube", "social", "Видео, просмотры, удержание, источники и идеи контента.", "oauth2", "3 минуты", "GOOGLE", scopes=("https://www.googleapis.com/auth/youtube.readonly",), auth_url="https://accounts.google.com/o/oauth2/v2/auth", docs_url="https://developers.google.com/youtube/v3"),
    IntegrationSpec("mailchimp", "Mailchimp", "email", "Email-кампании, аудитории, клики и доход от рассылок.", "api_key", "2 минуты", "MAILCHIMP", docs_url="https://mailchimp.com/developer/marketing/"),
    IntegrationSpec("brevo", "Brevo", "email", "Email/SMS кампании, контакты, клики и конверсии.", "api_key", "2 минуты", "BREVO", docs_url="https://developers.brevo.com/"),
    IntegrationSpec("klaviyo", "Klaviyo", "email", "Email/SMS, ecommerce-события и revenue attribution.", "api_key", "2 минуты", "KLAVIYO", docs_url="https://developers.klaviyo.com/"),
    IntegrationSpec("meta_pixel", "Meta Pixel", "pixels", "События сайта для ретаргетинга и оптимизации Meta Ads.", "install_snippet", "1 минута", "META_PIXEL", install_steps=("Скопируйте Pixel ID из Events Manager.", "Добавьте ID в настройки сайта или GTM.", "Проверьте событие PageView и Lead."), docs_url="https://developers.facebook.com/docs/meta-pixel/"),
    IntegrationSpec("tiktok_pixel", "TikTok Pixel", "pixels", "События сайта для TikTok Ads и оптимизации конверсий.", "install_snippet", "1 минута", "TIKTOK_PIXEL", install_steps=("Скопируйте Pixel ID из TikTok Events Manager.", "Установите через сайт или GTM.", "Проверьте PageView и SubmitForm."), docs_url="https://business-api.tiktok.com/portal/docs?id=1739584855420929"),
    IntegrationSpec("gtm", "Google Tag Manager", "pixels", "Единая установка тегов, пикселей, событий и конверсий.", "install_snippet", "1 минута", "GTM", install_steps=("Создайте контейнер GTM.", "Добавьте GTM ID на сайт.", "Установите теги GA4, Meta Pixel, TikTok Pixel и TrafficMind."), docs_url="https://developers.google.com/tag-platform/tag-manager"),
    IntegrationSpec("call_tracking", "Call Tracking", "calls", "Звонки, источник звонка, качество обращения и связь с CRM.", "webhook_or_api_key", "5 минут", "CALL_TRACKING", user_fields=("Название сервиса: Calltouch, CallRail, Roistat или другой", "API ключ или webhook URL"), install_steps=("Создайте webhook на стороне call tracking сервиса.", "Укажите URL TrafficMind для приема звонков.", "Сопоставьте номер, источник и сделку в CRM.")),
]


def get_integration(code: str) -> IntegrationSpec | None:
    return next((item for item in INTEGRATIONS if item.code == code), None)


def integrations_by_category(category: str) -> list[IntegrationSpec]:
    return [item for item in INTEGRATIONS if item.category == category]


def grouped_integrations() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in INTEGRATIONS:
        grouped.setdefault(item.category, []).append(integration_to_dict(item))
    return grouped


def integration_to_dict(item: IntegrationSpec) -> dict:
    return {
        "code": item.code,
        "title": item.title,
        "category": item.category,
        "category_title": CATEGORY_TITLES[item.category],
        "purpose": item.purpose,
        "auth_type": item.auth_type,
        "setup_time": item.setup_time,
        "required_env": required_env_vars(item),
        "docs_url": item.docs_url,
        "user_fields": list(item.user_fields),
        "install_steps": list(item.install_steps),
    }


def required_env_vars(item: IntegrationSpec) -> list[str]:
    if item.auth_type != "oauth2":
        return []
    if item.env_prefix == "GOOGLE":
        return ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]
    return [f"{item.env_prefix}_CLIENT_ID", f"{item.env_prefix}_CLIENT_SECRET", f"{item.env_prefix}_REDIRECT_URI"]


def build_oauth_url(item: IntegrationSpec, client_id: str, redirect_uri: str, state: str) -> str | None:
    if item.auth_type != "oauth2" or not item.auth_url:
        return None
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }
    if item.scopes:
        params["scope"] = " ".join(item.scopes)
    if item.env_prefix == "GOOGLE":
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    return f"{item.auth_url}?{urlencode(params)}"
