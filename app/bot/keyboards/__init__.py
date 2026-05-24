from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Dashboard", callback_data="dashboard"),
            InlineKeyboardButton(text="Карта прибыли", callback_data="profit_map"),
        ],
        [
            InlineKeyboardButton(text="Что делать сегодня", callback_data="today_actions"),
            InlineKeyboardButton(text="Потери", callback_data="losses"),
        ],
        [
            InlineKeyboardButton(text="AI-маркетолог", callback_data="ask_ai"),
            InlineKeyboardButton(text="Content AI", callback_data="content_ai"),
        ],
        [
            InlineKeyboardButton(text="AI Growth Council", callback_data="ai_council"),
        ],
        [
            InlineKeyboardButton(text="Конкуренты", callback_data="competitors"),
            InlineKeyboardButton(text="Отчеты", callback_data="report"),
        ],
        [
            InlineKeyboardButton(text="Отчет по ссылке", callback_data="link_only_report"),
            InlineKeyboardButton(text="Личный кабинет", callback_data="account_link"),
        ],
        [
            InlineKeyboardButton(text="Интеграции", callback_data="integrations"),
            InlineKeyboardButton(text="Подписка", callback_data="subscription"),
        ],
        [
            InlineKeyboardButton(text="Добавить сайт", callback_data="add_site"),
            InlineKeyboardButton(text="Бесплатный аудит", callback_data="audit"),
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
