# TrafficMind TrueMetrics

Бесплатный self-hosted инструмент аналитики для TrafficMind AI.

## Что внутри

- PostHog self-hosted — глубокая продуктовая аналитика, события, funnels, retention, session replay при включении.
- Собственный server-side collector — честный сбор событий с сайта и из бота.
- ClickHouse — независимое хранилище сырых событий, чтобы не зависеть только от внешней панели.
- Browser tracker `public/tm.js` — pageview, click, scroll, UTM.
- Bot SDK `src/sdk.ts` — события из TrafficMind AI.

## Почему это правдивее обычной JS-метрики

Обычный счётчик видит только то, что прошло через браузер. Здесь есть два слоя:

1. Browser events: поведение на сайте.
2. Server events: события из бота, backend, CRM, формы, лиды.

Плюс система отдельно помечает ботов, хранит `source=browser/server`, считает `truth-score` и позволяет сравнивать данные.

## Быстрый запуск collector + ClickHouse

```bash
cp .env.example .env
docker compose up --build
```

Проверка:

```bash
curl http://localhost:8088/health
```

## Установка счётчика на сайт

```html
<script
  async
  src="https://your-domain.com/static/tm.js"
  data-endpoint="https://your-domain.com/collect"
  data-project="trafficmind-ai"
  data-site="main-site">
</script>
```

Кастомное событие:

```js
window.TrafficMindMetrics.track('signup_click', { plan: 'pro' })
```

## Событие из TrafficMind AI

```ts
import { TrafficMindMetricsClient } from './src/sdk';

const metrics = new TrafficMindMetricsClient({
  endpoint: 'https://metrics.your-domain.com',
  secret: process.env.COLLECTOR_SECRET!,
  projectId: 'trafficmind-ai',
  siteId: 'bot',
});

await metrics.track('lead_created', {
  userId: 'user_123',
  properties: { source: 'telegram', value: 100 }
});
```

## API отчётов

Все отчёты требуют:

```http
Authorization: Bearer <COLLECTOR_SECRET>
```

### Summary

```bash
curl -H "Authorization: Bearer change_me_long_random_secret" \
  "http://localhost:8088/reports/summary?projectId=trafficmind-ai&days=7"
```

### Sources

```bash
curl -H "Authorization: Bearer change_me_long_random_secret" \
  "http://localhost:8088/reports/sources?projectId=trafficmind-ai&days=7"
```

### Pages

```bash
curl -H "Authorization: Bearer change_me_long_random_secret" \
  "http://localhost:8088/reports/pages?projectId=trafficmind-ai&days=7"
```

### Truth score

```bash
curl -H "Authorization: Bearer change_me_long_random_secret" \
  "http://localhost:8088/reports/truth-score?projectId=trafficmind-ai&days=7"
```

## PostHog

PostHog self-hosted лучше ставить отдельно официальным способом:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/posthog/posthog/HEAD/bin/deploy-hobby)"
```

После установки укажи в `.env`:

```env
POSTHOG_ENABLED=true
POSTHOG_HOST=https://posthog.your-domain.com
POSTHOG_PROJECT_API_KEY=ph_project_token_here
```

Collector будет сохранять события в ClickHouse и параллельно отправлять их в PostHog.

## Что попросить Codex сделать дальше

1. Встроить `TrafficMindMetricsClient` в backend бота.
2. На каждое важное действие отправлять event:
   - `bot_message_received`
   - `lead_created`
   - `report_generated`
   - `payment_started`
   - `payment_success`
   - `campaign_created`
   - `traffic_audit_requested`
3. Подключить `tm.js` на сайт.
4. Добавить admin dashboard поверх `/reports/*`.
5. Добавить импорт nginx/access logs для сравнения с browser events.
