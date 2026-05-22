# Integrations Setup

Цель: пользователь в Telegram выбирает категорию, сервис и получает максимально короткое подключение.

## UX flow

1. Пользователь нажимает `Интеграции`.
2. Выбирает категорию: аналитика, реклама, CRM, соцсети, email, пиксели, call tracking.
3. Выбирает сервис.
4. Бот показывает:
   - зачем нужен сервис;
   - сколько займет подключение;
   - тип подключения;
   - кнопку OAuth, если `.env` настроен;
   - короткую инструкцию, если нужен API-ключ, пиксель, GTM или webhook.

## OAuth services

Для OAuth нужны client credentials в `.env`. Без них бот не может выдавать реальную ссылку авторизации.

Google services use:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Meta services use:

- `META_CLIENT_ID`
- `META_CLIENT_SECRET`
- `META_REDIRECT_URI`

Other prefixes:

- `YANDEX_*`
- `VK_*`
- `TIKTOK_*`
- `LINKEDIN_*`
- `HUBSPOT_*`
- `BITRIX24_*`
- `AMOCRM_*`

Новые OAuth-сервисы:

- `YANDEX_*` используется и для Яндекс Метрики, и для Яндекс Директа. Для Директа приложение должно иметь доступ к Direct API.
- `VK_*` используется для VK API: сообщества, публикации, статистика и рекламные данные VK.

## Current implementation status

Implemented:

- integration registry;
- Telegram category picker;
- Telegram service picker;
- setup/instruction card;
- OAuth URL generation when env vars exist;
- OAuth code-to-token exchange for providers with token endpoint;
- OAuth callback receiver;
- database status `connected` after successful token exchange;
- API catalog endpoints.

Next production step:

- provider-specific token exchange;
- encrypted token storage;
- sync jobs per provider;
- normalized metric ingestion;
- user-facing connection status dashboard.
