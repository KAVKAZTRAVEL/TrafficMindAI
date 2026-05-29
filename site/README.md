# TrafficMind AI Site

This folder is the standalone website version of TrafficMind AI.

It includes:

- main product page: `index.html`
- generated demo report: `report.html`
- tariffs: `tariffs.html`
- client cabinet: `account.html`
- owner/admin demo: `admin.html`
- shared visual style: `trafficmind_unified.css`
- local API server: `server.js`
- account/auth helpers: `backend.js`
- client cabinet logic: `account.js`
- client cabinet styles: `account.css`

The Telegram bot is not part of this folder. It can be added later as a separate channel that reads the same user settings and reports.

## Local Start

```bash
cd site
node server.js
```

Open:

```text
http://127.0.0.1:4174/
```

## Local API

The local server now includes a first working account layer:

- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/account/settings`
- `POST /api/account/settings`
- `POST /api/account/telegram-code`
- `GET /api/reports/link-only-demo?domain=example.com`
- `GET /api/growth/demo`
- `GET /api/ai-council/demo`
- `GET /api/integrations`
- `POST /api/integrations/:code/setup`
- `POST /billing/stripe/checkout`

User accounts, sessions and settings are stored in `site/.runtime/trafficmind-db.json`.
That folder is ignored by git and should be replaced by a real database before scaling.

Stripe checkout is no longer faked. If `STRIPE_SECRET_KEY` and
`STRIPE_PRICE_PRO_399` are missing, the API returns a clear setup error.

OAuth integrations are no longer marked as connected by default. They report
`credentials_required`, `ready_to_connect`, `snippet_required`, or `connected`.
Provider-specific OAuth callback implementation is still a launch task.

## Future Bot Connection

The future Telegram bot should be developed outside this folder and then connected through backend endpoints:

- account sync
- report delivery
- alerts
- billing status
- user settings

This keeps the website launch independent from the Telegram bot launch.
