# TrafficMind AI: запуск сначала сайта, потом Telegram

## Что изменилось

Сайт отделен в папку `site/`. Его можно запускать, тестировать и деплоить отдельно от Telegram-бота.

Telegram остается будущим каналом доставки отчетов и алертов, но не блокирует запуск web-продукта.

## Что входит в первый web-запуск

- `site/index.html` - главная страница продукта.
- `site/report.html` - отчет после проверки ссылки.
- `site/tariffs.html` - тарифы.
- `site/account.html` - личный кабинет клиента.
- `site/admin.html` - demo/internal панель владельца.
- `site/server.js` - локальный demo API.
- `site/privacy.html`, `site/terms.html`, `site/security.html` - базовые legal/security страницы.
- `site/robots.txt`, `site/sitemap.xml` - базовая SEO-инфраструктура.

## Локальный запуск только сайта

```bash
cd site
node server.js
```

Открыть:

```text
http://127.0.0.1:4174/
```

## GitHub Pages

Workflow `.github/workflows/pages.yml` публикует только папку `site/`.

Онлайн-адрес после деплоя:

```text
https://kavkaztravel.github.io/TrafficMindAI/
```

## Что остается demo-режимом

- Проверка сайта по ссылке показывает demo-preview.
- Интеграции перечислены, но реальные OAuth-подключения требуют backend.
- Личный кабинет сохраняет часть данных локально в браузере.
- Админка является demo/internal экраном, не production auth.
- AI Growth Council работает в demo/fallback режиме без реальных model API ключей.

## Что нужно для коммерческого SaaS

- Production backend hosting.
- PostgreSQL.
- Регистрация и вход пользователей.
- Защищенная админка.
- Биллинг и webhooks.
- Реальные OAuth-интеграции.
- Шифрование токенов.
- Мониторинг ошибок и uptime.

## Telegram позже

Когда web-продукт стабилен:

1. Создаем Telegram-бота в BotFather.
2. Подключаем `TELEGRAM_BOT_TOKEN`.
3. Добавляем команду `/account` для одноразового кода.
4. Связываем Telegram ID с web-кабинетом.
5. Отправляем отчеты и алерты в чат.
