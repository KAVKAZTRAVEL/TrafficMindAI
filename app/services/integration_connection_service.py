import os
from dataclasses import dataclass
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.registry import (
    CATEGORY_TITLES,
    build_oauth_url,
    get_integration,
    integration_to_dict,
    integrations_by_category,
    required_env_vars,
)
from app.models import IntegrationAccount, User


@dataclass(frozen=True)
class IntegrationSetup:
    title: str
    text: str
    connect_url: str | None
    docs_url: str | None
    status: str


def categories_text() -> str:
    return "\n".join(f"- {title}" for title in CATEGORY_TITLES.values())


def category_summary(category: str) -> str:
    items = integrations_by_category(category)
    title = CATEGORY_TITLES.get(category, category)
    lines = [f"{title}\n"]
    for item in items:
        lines.append(f"- {item.title}: {item.purpose}")
    return "\n".join(lines)


def env_value(name: str) -> str:
    return os.getenv(name, "").strip()


def oauth_env(item) -> tuple[str, str]:
    required = required_env_vars(item)
    if not required:
        return "", ""
    return env_value(required[0]), env_value(required[2])


def oauth_secret(item) -> str:
    required = required_env_vars(item)
    if len(required) < 2:
        return ""
    return env_value(required[1])


async def prepare_integration_setup(session: AsyncSession, user: User, code: str) -> IntegrationSetup:
    item = get_integration(code)
    if not item:
        return IntegrationSetup("Интеграция не найдена", "Такого сервиса нет в каталоге.", None, None, "missing")

    account = await session.scalar(
        select(IntegrationAccount).where(IntegrationAccount.user_id == user.id, IntegrationAccount.provider == item.code)
    )
    if not account:
        account = IntegrationAccount(
            user_id=user.id,
            provider=item.code,
            category=item.category,
            status="pending_setup",
            scopes=list(item.scopes),
        )
        session.add(account)
        await session.commit()

    connect_url = None
    missing = []
    if item.auth_type == "oauth2":
        required = required_env_vars(item)
        missing = [name for name in required if not env_value(name)]
        client_id, redirect_uri = oauth_env(item)
        if not missing:
            connect_url = build_oauth_url(item, client_id, redirect_uri, state=f"{user.id}:{item.code}")

    text = setup_text(item, bool(connect_url), missing)
    return IntegrationSetup(item.title, text, connect_url, item.docs_url, account.status)


def setup_text(item, has_oauth_url: bool, missing_env: list[str]) -> str:
    base = [
        f"{item.title}",
        "",
        item.purpose,
        f"Тип подключения: {auth_type_label(item.auth_type)}.",
        f"Обычно занимает: {item.setup_time}.",
    ]
    if item.auth_type == "oauth2":
        if has_oauth_url:
            base += ["", "Нажмите кнопку подключения, войдите в сервис и разрешите доступ только на чтение/аналитику."]
        else:
            base += [
                "",
                "Для OAuth нужно один раз добавить ключи приложения в .env:",
                ", ".join(missing_env),
                "После этого бот начнет выдавать прямую кнопку подключения.",
            ]
    elif item.auth_type == "api_key":
        base += ["", "Самый простой путь: пользователь вставляет API-ключ в защищенную форму/админку. В Telegram показываем короткую инструкцию, где его взять."]
    elif item.auth_type == "install_snippet":
        base += ["", "Установка без OAuth:", *[f"{index}. {step}" for index, step in enumerate(item.install_steps, start=1)]]
    else:
        base += ["", "Подключение через webhook или API-ключ:", *[f"{index}. {step}" for index, step in enumerate(item.install_steps, start=1)]]
    if item.user_fields:
        base += ["", "Что нужно от пользователя:", *[f"- {field}" for field in item.user_fields]]
    if item.docs_url:
        base += ["", f"Документация: {item.docs_url}"]
    return "\n".join(base)


def auth_type_label(auth_type: str) -> str:
    return {
        "oauth2": "вход через аккаунт",
        "api_key": "API-ключ",
        "install_snippet": "установка пикселя/тега",
        "webhook_or_api_key": "webhook или API-ключ",
    }.get(auth_type, auth_type)


async def exchange_oauth_code(item, code: str) -> dict:
    if item.auth_type != "oauth2" or not item.token_url:
        raise ValueError("Для этой интеграции не настроен OAuth token endpoint.")
    client_id, redirect_uri = oauth_env(item)
    client_secret = oauth_secret(item)
    if not client_id or not client_secret or not redirect_uri:
        missing = [name for name in required_env_vars(item) if not env_value(name)]
        raise ValueError(f"Не хватает env-переменных: {', '.join(missing)}")

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        if item.token_method.upper() == "GET":
            response = await client.get(item.token_url, params=payload)
        else:
            response = await client.post(item.token_url, data=payload)
        response.raise_for_status()
        token_payload = response.json()

    if "access_token" not in token_payload:
        raise ValueError("Сервис не вернул access_token.")
    return token_payload


def catalog_payload() -> dict:
    return {
        "categories": CATEGORY_TITLES,
        "integrations": {
            category: [integration_to_dict(item) for item in integrations_by_category(category)]
            for category in CATEGORY_TITLES
        },
    }
