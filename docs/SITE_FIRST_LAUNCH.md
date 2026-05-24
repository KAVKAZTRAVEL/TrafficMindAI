# TrafficMind AI: запуск сначала сайта, потом Telegram-бота

## Цель разделения

Проект теперь можно запускать в два этапа:

1. **Сайт и web-кабинет** - запускаются первыми и не требуют Telegram-токена.
2. **Telegram-бот** - подключается позже отдельным compose profile, когда будет готов BotFather token и сценарии сообщений.

Так можно быстрее вывести продукт наружу: показать сайт, тарифы, личный кабинет, отчет по ссылке, интеграции, AI Growth Council и демо-аналитику, а Telegram оставить как следующий канал доставки отчетов.

## Что входит в первый запуск сайта

- Главная продающая страница: `demo/link_only_report.html`.
- Личный кабинет клиента: `demo/account.html`.
- Тарифы: `demo/tariffs.html`.
- Админ-демо: `demo/admin.html`.
- API health checks.
- Demo growth intelligence.
- Demo AI Growth Council.
- Каталог интеграций.
- Отчет по ссылке.
- Tracker endpoint.
- Billing endpoints.

Telegram при этом не стартует и не ломает запуск, даже если `TELEGRAM_BOT_TOKEN` пустой.

## Локальный статический запуск сайта

Подходит для просмотра дизайна, тарифов и клиентского сценария без backend:

```bash
node demo/demo_server.js
```

Открыть:

```text
http://127.0.0.1:4174/
http://127.0.0.1:4174/account.html
http://127.0.0.1:4174/tariffs.html
```

## Запуск сайта с backend

Подходит для проверки API, личного кабинета, отчетов, health checks и будущей production-инфраструктуры:

```bash
docker compose up --build
```

Открыть:

```text
http://localhost:8000/demo/link_only_report.html
http://localhost:8000/demo/account.html
http://localhost:8000/demo/tariffs.html
http://localhost:8000/health
http://localhost:8000/api/ai-council/demo
http://localhost:8000/api/integrations
```

## Запуск Telegram-бота позже

Когда будет создан бот в BotFather и заполнен `TELEGRAM_BOT_TOKEN`, запускай:

```bash
docker compose --profile telegram up --build
```

Этот профиль добавит сервис `bot`, но не меняет сайт и API.

## Что нужно заполнить для первого запуска сайта

Минимально:

```env
ENVIRONMENT=local
PUBLIC_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://trafficmind:trafficmind@postgres:5432/trafficmind
SYNC_DATABASE_URL=postgresql://trafficmind:trafficmind@postgres:5432/trafficmind
REDIS_URL=redis://redis:6379/0
AI_COUNCIL_MODE=demo
```

Можно оставить пустыми на первом этапе:

```env
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
GROK_API_KEY=
STRIPE_SECRET_KEY=
```

## Что нужно для подключения Telegram позже

```env
TELEGRAM_BOT_TOKEN=token_from_botfather
ADMIN_TELEGRAM_IDS=your_numeric_telegram_id
PUBLIC_BASE_URL=https://your-domain.com
```

После этого:

1. Пользователь нажимает `/account` в Telegram.
2. Бот выдает одноразовый код.
3. Пользователь вводит код в `account.html`.
4. Кабинет и Telegram-профиль связываются.

## Архитектурное разделение

- `demo/*` - сайт, презентация, кабинет и demo UI.
- `app/main.py` - web API, demo endpoints, billing, integrations, reports.
- `app/services/*` - бизнес-логика, AI Growth Council, отчеты и тарифы.
- `app/bot/*` - Telegram UX, запускается только через profile `telegram`.
- `docker-compose.yml` - сайт/API по умолчанию, бот только по запросу.
