# TrafficMind AI: site-first structure

## Current separation

`site/` is now the independent website package. It can be launched, tested and deployed without running the Telegram bot.

`app/` remains the backend and future SaaS/API layer.

`app/bot/` remains the future Telegram channel and should not block the website launch.

## Site package

The site package contains:

- `site/index.html` - main website
- `site/report.html` - demo report after a link check
- `site/tariffs.html` - tariff presentation
- `site/account.html` - client cabinet
- `site/admin.html` - owner/admin demo
- `site/server.js` - local demo API and static server
- `site/trafficmind_unified.css` - shared approved visual style

## Run only the site

```bash
cd site
node server.js
```

Then open:

```text
http://127.0.0.1:4174/
```

## Deploy only the site

GitHub Pages now uploads the `site/` folder only.

For a production SaaS launch with working API, use a Node/Python hosting provider for backend endpoints. GitHub Pages is enough for the static website, but not for real OAuth integrations, billing webhooks, databases or scheduled analytics jobs.

## Telegram later

The Telegram bot can be added later without redesigning the site:

1. User creates a website account.
2. User connects services and sees reports on the website.
3. Later the Telegram bot issues a short sync code.
4. The website account and Telegram user are linked.
5. Bot sends report summaries, alerts and action plans.
