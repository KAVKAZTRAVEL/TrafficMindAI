# TrafficMind AI

MVP Telegram SaaS-бота по ТЗ: авторизация через Telegram ID, 7-дневный trial, тарифы, добавление сайтов, базовый аудит, AI Tracking Script, сбор событий, динамические источники трафика, Traffic Quality Score, Traffic Map HTML, отчеты и фоновые задачи.

## Быстрый запуск

1. Скопируйте `.env.example` в `.env`.
2. Вставьте `TELEGRAM_BOT_TOKEN`.
3. При необходимости укажите `ADMIN_TELEGRAM_IDS` через запятую. Это задел под будущую админ-панель владельца.
4. Запустите:

```bash
docker compose up --build
```

API будет доступен на `http://localhost:8000`, бот начнет polling, tracker endpoint: `POST /tracker/event`.

## Что уже реализовано

- `/start` создает пользователя по Telegram ID и включает trial.
- `/add_site` добавляет домен с лимитом по тарифу.
- `/audit` проверяет доступность сайта, CMS, формы, аналитику, базовое SEO и контакты.
- `/traffic_map` агрегирует реальные referrer/UTM-источники, считает Traffic Quality Score и строит HTML-карту.
- AI Tracking Script находится в `app/tracker/tracker.js` и отправляет page view, scroll, click, form submit и custom events.
- `app/admin` и защищенный `/admin/summary` оставлены как отдельная зона для будущей админ-панели владельца.

## Установка tracker

После добавления сайта бот выдаст строку:

```html
<script async src="http://localhost:8000/static/tracker.js" data-token="TOKEN" data-endpoint="http://localhost:8000/tracker/event"></script>
```

Добавьте ее перед `</body>` на сайте клиента.

## Архитектура

- `app/bot` - Telegram UX на aiogram 3.
- `app/services` - аудит, трафик, скоринг, AI-рекомендации, PDF и Traffic Map.
- `app/tracker` - легкий JS tracker и FastAPI endpoint.
- `app/models` - SQLAlchemy-модели под PostgreSQL.
- `app/jobs` - Celery-задачи для отчетов, подписок и smart alerts.
- `app/admin` - будущая админ-панель и статистика владельца.

## Admin API

Для первого защищенного доступа укажите свой Telegram ID:

```env
ADMIN_TELEGRAM_IDS=123456789
```

Запрос статистики:

```bash
curl -H "X-Admin-Telegram-Id: 123456789" http://localhost:8000/admin/summary
```

## Важно для продакшена

Перед запуском на реальных клиентах нужно подключить настоящие Telegram Payments/Stripe webhooks, защищенную авторизацию `/admin/*`, GA4 OAuth, хранение OAuth-токенов в секретном хранилище и генерацию PNG через Playwright в worker.
