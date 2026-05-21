from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.integrations.registry import CATEGORY_TITLES, get_integration, integrations_by_category


def integration_categories_keyboard() -> InlineKeyboardMarkup:
    rows = []
    categories = list(CATEGORY_TITLES.items())
    for index in range(0, len(categories), 2):
        chunk = categories[index : index + 2]
        rows.append([InlineKeyboardButton(text=title, callback_data=f"int_cat:{code}") for code, title in chunk])
    rows.append([InlineKeyboardButton(text="Назад в меню", callback_data="dashboard")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def integrations_list_keyboard(category: str) -> InlineKeyboardMarkup:
    rows = []
    items = integrations_by_category(category)
    for index in range(0, len(items), 2):
        chunk = items[index : index + 2]
        rows.append([InlineKeyboardButton(text=item.title, callback_data=f"int_svc:{item.code}") for item in chunk])
    rows.append([InlineKeyboardButton(text="Все категории", callback_data="integrations")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def integration_setup_keyboard(code: str, connect_url: str | None, docs_url: str | None) -> InlineKeyboardMarkup:
    item = get_integration(code)
    rows = []
    if connect_url:
        rows.append([InlineKeyboardButton(text=f"Подключить {item.title if item else 'сервис'}", url=connect_url)])
    rows.append([InlineKeyboardButton(text="Я подключил, проверить", callback_data=f"int_check:{code}")])
    if docs_url:
        rows.append([InlineKeyboardButton(text="Открыть инструкцию сервиса", url=docs_url)])
    if item:
        rows.append([InlineKeyboardButton(text="Назад к категории", callback_data=f"int_cat:{item.category}")])
    rows.append([InlineKeyboardButton(text="Все интеграции", callback_data="integrations")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
