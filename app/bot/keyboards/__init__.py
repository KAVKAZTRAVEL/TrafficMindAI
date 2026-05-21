from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Добавить сайт", callback_data="add_site"),
            InlineKeyboardButton(text="Бесплатный аудит", callback_data="audit"),
        ],
        [
            InlineKeyboardButton(text="Карта трафика", callback_data="traffic_map"),
            InlineKeyboardButton(text="Мой отчет", callback_data="report"),
        ],
        [
            InlineKeyboardButton(text="Спросить ИИ", callback_data="ask_ai"),
            InlineKeyboardButton(text="Проверить всё", callback_data="check_all"),
        ],
        [
            InlineKeyboardButton(text="Найти проблему", callback_data="find_problem"),
            InlineKeyboardButton(text="Подписка", callback_data="subscription"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="START 199 ₽", callback_data="plan_START")],
            [InlineKeyboardButton(text="BUSINESS 299 ₽", callback_data="plan_BUSINESS")],
            [InlineKeyboardButton(text="AGENCY 999 ₽", callback_data="plan_AGENCY")],
        ]
    )
