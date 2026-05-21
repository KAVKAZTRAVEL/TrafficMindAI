from aiogram import Dispatcher
from app.bot.handlers.core import router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
