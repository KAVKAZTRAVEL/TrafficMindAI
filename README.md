# TrafficMind AI

TrafficMind AI - AI-платформа роста для бизнеса в формате Telegram-бота и будущего web dashboard. Проект развивается от MVP аналитического бота к enterprise SaaS между HubSpot, SimilarWeb, Google Analytics, SEMrush, Hotjar и AI-маркетологом.

Главная идея: система не заставляет пользователя вручную анализировать цифры. Она сама отвечает:

- что происходит;
- почему это происходит;
- насколько это критично;
- что делать первым;
- какой эффект даст действие;
- что прогнозируется дальше;
- где теряются деньги;
- какие возможности роста есть сейчас.

## Онлайн-демо

[https://kavkaztravel.github.io/TrafficMindAI/demo/traffic_map_demo.html](https://kavkaztravel.github.io/TrafficMindAI/demo/traffic_map_demo.html)

## Новая структура продукта

- Dashboard - деньги, риски, рост и план на сегодня.
- Карта прибыли - доход, лиды, продажи, ROI, ROAS и пути пользователя.
- Аудит - сайт, SEO, формы, скорость, пиксели, аналитика и CRM готовность.
- Потери - каналы, страницы и этапы воронки, где теряются деньги.
- AI-маркетолог - причины, аномалии, корреляции, рекомендации.
- Что делать сегодня - задачи с эффектом, сложностью, приоритетом и влиянием на доход.
- Content AI - посты, Reels, объявления, email, CTA и SEO-контент.
- Конкуренты - страницы, ключевые слова, объявления, соцсети и идеи роста.
- Прогнозы - лиды, доход, CPL, ROAS и сценарии бюджета.
- Отчеты - Telegram summaries, PDF, PNG и регулярные отчеты.
- Интеграции - аналитика, реклама, CRM, соцсети, email и пиксели.
- Подписка - trial, тарифы и лимиты.

## Быстрый запуск

1. Скопируйте `.env.example` в `.env`.
2. Вставьте `TELEGRAM_BOT_TOKEN`.
3. Укажите `ADMIN_TELEGRAM_IDS` через запятую для доступа владельца.
4. Запустите:

```bash
docker compose up --build
```

API будет доступен на `http://localhost:8000`, бот начнет polling, tracker endpoint: `POST /tracker/event`.

## Рабочие API

- `GET /health` - health check.
- `GET /api/growth/demo` - демонстрация enterprise intelligence layer: карта прибыли, insights, задачи и прогноз.
- `POST /tracker/event` - прием событий AI Tracking Script.
- `GET /admin/summary` - защищенная статистика владельца через `X-Admin-Telegram-Id`.

## Что уже реализовано в коде

- Telegram-авторизация по Telegram ID.
- 7-дневный trial.
- Тарифы и лимиты сайтов.
- Добавление сайта.
- Базовый аудит сайта.
- AI Tracking Script.
- Прием событий tracker.
- Агрегация источников.
- Traffic Quality Score.
- Карта прибыли / карта источников в HTML.
- PDF-отчет.
- Growth intelligence layer:
  - нормализованные метрики каналов;
  - карта прибыли;
  - поиск потерь;
  - задачи "что делать сегодня";
  - прогноз дохода.
- Enterprise docs:
  - `docs/ENTERPRISE_PRODUCT_BLUEPRINT.md`
  - `docs/UX_UI_STRUCTURE.md`
  - `docs/DATABASE_DESIGN.md`
  - `docs/ROADMAP.md`

## Архитектура

- `app/bot` - Telegram UX на aiogram 3.
- `app/services` - аудит, трафик, скоринг, AI-рекомендации, карта прибыли, PDF и growth intelligence.
- `app/tracker` - легкий JS tracker и FastAPI endpoint.
- `app/models` - SQLAlchemy-модели под PostgreSQL.
- `app/jobs` - Celery-задачи для отчетов, подписок и smart alerts.
- `app/integrations` - слой внешних интеграций.
- `app/admin` - будущая админ-панель и статистика владельца.
- `docs` - enterprise спецификация продукта.

## Интеграции в roadmap

- Google Analytics 4.
- Google Search Console.
- Яндекс Метрика.
- Google Ads.
- Meta Ads.
- TikTok Ads.
- LinkedIn Ads.
- HubSpot.
- Bitrix.
- AmoCRM.
- Instagram, TikTok, Facebook, LinkedIn, YouTube.
- Mailchimp, Brevo, Klaviyo.
- Meta Pixel, TikTok Pixel, Google Tag Manager.
- Call Tracking.

## Установка tracker

После добавления сайта бот выдаст строку:

```html
<script async src="http://localhost:8000/static/tracker.js" data-token="TOKEN" data-endpoint="http://localhost:8000/tracker/event"></script>
```

Добавьте ее перед `</body>` на сайте клиента.

## Admin API

```env
ADMIN_TELEGRAM_IDS=123456789
```

```bash
curl -H "X-Admin-Telegram-Id: 123456789" http://localhost:8000/admin/summary
```

## Production TODO

- Alembic migrations вместо `create_all`.
- Защищенная web admin auth.
- OAuth flows для реальных интеграций.
- Webhooks Telegram Payments и Stripe.
- Шифрование OAuth-токенов.
- Очереди ingestion по расписанию.
- Sentry/Prometheus/Grafana.
- PNG-рендер карты через Playwright.
- RBAC и organization/team модель.
