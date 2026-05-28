# TrafficMind AI

## Standalone website package

The website is now separated into `site/` so it can be launched and developed independently from the future Telegram bot.

Run only the site:

```bash
cd site
node server.js
```

Open:

```text
http://127.0.0.1:4174/
```

GitHub Pages deploys only the `site/` folder. The bot remains in `app/bot/` and can be connected later.

## Site-first launch mode

Проект разделен на два этапа запуска:

- **Сначала сайт и web-кабинет**: главная страница, тарифы, личный кабинет, demo-отчеты, API, интеграции и AI Growth Council работают без Telegram-токена.
- **Потом Telegram-бот**: запускается отдельно, когда будет готов `TELEGRAM_BOT_TOKEN`.

Команды:

```bash
# сайт + API без Telegram-бота
docker compose up --build

# сайт + API + Telegram-бот
docker compose --profile telegram up --build

# standalone сайт
cd site
node server.js
```

Подробнее: [`docs/SITE_FIRST_LAUNCH.md`](docs/SITE_FIRST_LAUNCH.md)

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

[https://kavkaztravel.github.io/TrafficMindAI/](https://kavkaztravel.github.io/TrafficMindAI/)

Дополнительные demo-экраны:

- [Личный кабинет](https://kavkaztravel.github.io/TrafficMindAI/account.html)
- [Тарифы](https://kavkaztravel.github.io/TrafficMindAI/tariffs.html)
- [Полный demo-preview отчета](https://kavkaztravel.github.io/TrafficMindAI/report.html?domain=example.com&plan=trial)
- [Политика конфиденциальности](https://kavkaztravel.github.io/TrafficMindAI/privacy.html)
- [Условия использования](https://kavkaztravel.github.io/TrafficMindAI/terms.html)

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
- `GET /api/account/demo` - демо-данные личного кабинета.
- `GET /api/account/{telegram_id}` - сохраненный личный кабинет пользователя.
- `POST /api/account/settings` - сохранить настройки личного кабинета один раз и использовать дальше.
- `GET /api/reports/link-only-demo?domain=example.com` - имитация полного отчета, когда клиент просто отправляет ссылку на сайт без подключений.
- `GET /admin/alerts-demo?domain=example.com` - owner/admin alerts по отчету: горячие лиды, риск оттока, денежные потери.
- `GET /api/integrations` - каталог всех интеграций с категориями и типами подключения.
- `GET /api/integrations/{code}/setup` - инструкция подключения конкретного сервиса.
- `GET /oauth/{provider}/callback` - прием OAuth callback и фиксация статуса `authorized_pending_token_exchange`.
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
- Отчет по ссылке без подключений:
  - предварительный executive summary;
  - онбординг "1 ссылка -> первый отчет -> подключить данные";
  - блок "что вижу / что не вижу";
  - оценка уверенности отчета;
  - технические и маркетинговые score;
  - гипотезы потерь;
  - модуль "Потери денег";
  - список действий на сегодня;
  - продающий HTML/PDF-артефакт;
  - честный список данных, которых не хватает без интеграций.
- Growth intelligence layer:
  - нормализованные метрики каналов;
  - карта прибыли;
  - поиск потерь;
  - задачи "что делать сегодня";
  - прогноз дохода.
- Центр интеграций в Telegram:
  - категории источников;
  - выбор сервиса;
  - OAuth-link при наличии client id/redirect uri;
  - короткие инструкции для API-ключей, пикселей, GTM и call tracking;
  - фиксация статуса подключения в базе.
- Личный кабинет:
  - профиль пользователя;
  - бизнес-контекст;
  - сайты;
  - подписка;
  - подключенные интеграции;
  - настройки отчетов и уведомлений;
  - сохранение через `POST /api/account/settings`.
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

Каталог уже добавлен в код. Для максимально простого подключения бот показывает путь по типам:

- OAuth: Google Analytics 4, Google Search Console, Яндекс Метрика, Google Ads, Meta Ads, TikTok Ads, LinkedIn Ads, HubSpot, Bitrix24, AmoCRM, Instagram, TikTok, Facebook, LinkedIn, YouTube.
- API-ключ: Mailchimp, Brevo, Klaviyo.
- Пиксель/тег: Meta Pixel, TikTok Pixel, Google Tag Manager.
- Webhook/API-ключ: Call Tracking.

Важно: OAuth-сервисы начнут выдавать прямую кнопку подключения после добавления client id, client secret и redirect uri в `.env`. Это требование самих платформ, без него нельзя легально получить доступ к данным аккаунта пользователя.

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
