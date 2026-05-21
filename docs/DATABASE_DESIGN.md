# Database Design

## Core

- `organizations` - компании и агентства.
- `users` - Telegram users и члены команды.
- `websites` - сайты и проекты.
- `subscriptions` - тарифы, статусы и лимиты.
- `integration_accounts` - подключенные внешние сервисы.
- `oauth_tokens` - зашифрованные токены интеграций.

## Events

- `marketing_events`
  - organization_id
  - website_id
  - visitor_id
  - session_id
  - event_type
  - source
  - medium
  - campaign
  - page_url
  - value
  - revenue
  - occurred_at

- `sessions`
- `page_views`
- `events`
- `conversions`

## Metrics

- `channel_metrics`
  - website_id
  - source
  - medium
  - campaign
  - period
  - spend
  - revenue
  - leads
  - sales
  - clicks
  - impressions
  - cpl
  - cpa
  - roas
  - roi
  - conversion_rate

- `funnel_steps`
- `profit_map_nodes`
- `profit_map_edges`
- `revenue_attribution`

## Intelligence

- `insights`
  - type
  - severity
  - confidence
  - title
  - explanation
  - evidence
  - created_at

- `action_items`
  - priority
  - expected_impact
  - revenue_impact
  - complexity
  - time_to_execute
  - status

- `forecasts`
  - metric
  - current_value
  - predicted_value
  - lower_bound
  - upper_bound
  - horizon_days

- `content_briefs`
- `competitor_snapshots`
- `competitor_content_items`

## Admin

- `system_logs`
- `integration_errors`
- `billing_events`
- `usage_events`
- `feature_flags`

## Tenant isolation

Каждая бизнес-сущность должна иметь `organization_id`. Для MVP можно продолжать использовать `user_id`, но enterprise-версия должна перейти на organization/team модель.
