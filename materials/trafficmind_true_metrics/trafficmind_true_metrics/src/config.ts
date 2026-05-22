import 'dotenv/config';

export const config = {
  port: Number(process.env.PORT || 8088),
  publicTrackingOrigin: process.env.PUBLIC_TRACKING_ORIGIN || '*',
  collectorSecret: process.env.COLLECTOR_SECRET || 'dev-secret',

  clickhouse: {
    url: process.env.CLICKHOUSE_URL || 'http://localhost:8123',
    username: process.env.CLICKHOUSE_USER || 'default',
    password: process.env.CLICKHOUSE_PASSWORD || '',
    database: process.env.CLICKHOUSE_DATABASE || 'trafficmind',
  },

  posthog: {
    enabled: String(process.env.POSTHOG_ENABLED || 'false') === 'true',
    host: process.env.POSTHOG_HOST || '',
    projectApiKey: process.env.POSTHOG_PROJECT_API_KEY || '',
  },

  ipHashSalt: process.env.IP_HASH_SALT || 'dev-salt',
  botUaDenylist: (process.env.BOT_UA_DENYLIST || 'bot,crawler,spider,preview,headless')
    .split(',')
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean),
};
