import asyncio
from aiogram import Bot, Dispatcher
from app.bot.handlers import register_handlers
from app.config import get_settings
from app.database import init_db


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")
    await init_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
