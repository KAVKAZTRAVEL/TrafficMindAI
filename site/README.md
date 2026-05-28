# TrafficMind AI Site

This folder is the standalone website version of TrafficMind AI.

It includes:

- main product page: `index.html`
- generated demo report: `report.html`
- tariffs: `tariffs.html`
- client cabinet: `account.html`
- owner/admin demo: `admin.html`
- shared visual style: `trafficmind_unified.css`
- local demo API server: `server.js`

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

## Demo API

The local server provides demo endpoints for testing the site without real integrations:

- `GET /health`
- `GET /api/reports/link-only-demo?domain=example.com`
- `GET /api/growth/demo`
- `GET /api/ai-council/demo`
- `GET /api/integrations`
- `GET /api/account/demo`

## Future Bot Connection

The future Telegram bot should be developed outside this folder and then connected through backend endpoints:

- account sync
- report delivery
- alerts
- billing status
- user settings

This keeps the website launch independent from the Telegram bot launch.
