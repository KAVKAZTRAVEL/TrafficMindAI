import { createClient } from '@clickhouse/client';
import { config } from './config.js';
import type { StoredEvent } from './types.js';

export const clickhouse = createClient({
  url: config.clickhouse.url,
  username: config.clickhouse.username,
  password: config.clickhouse.password,
  database: config.clickhouse.database,
});

export async function insertEvent(e: StoredEvent) {
  await clickhouse.insert({
    table: 'events',
    format: 'JSONEachRow',
    values: [{
      event_id: e.eventId,
      event_time: e.eventTime,
      received_at: e.receivedAt,
      project_id: e.projectId,
      site_id: e.siteId,
      event_name: e.event,
      visitor_id: e.visitorId,
      session_id: e.sessionId,
      user_id: e.userId,
      url: e.url,
      path: e.path,
      title: e.title,
      referrer: e.referrer,
      utm_source: e.utmSource,
      utm_medium: e.utmMedium,
      utm_campaign: e.utmCampaign,
      utm_content: e.utmContent,
      utm_term: e.utmTerm,
      ip_hash: e.ipHash,
      user_agent: e.userAgent,
      browser: e.browser,
      os: e.os,
      device: e.device,
      country: e.country,
      city: e.city,
      is_bot: e.isBot,
      bot_reason: e.botReason,
      source: e.source,
      properties: e.propertiesJson,
    }],
  });

  if (e.event === 'pageview') {
    await clickhouse.insert({
      table: 'pageviews',
      format: 'JSONEachRow',
      values: [{
        event_time: e.eventTime,
        project_id: e.projectId,
        site_id: e.siteId,
        visitor_id: e.visitorId,
        session_id: e.sessionId,
        url: e.url,
        path: e.path,
        referrer: e.referrer,
        utm_source: e.utmSource,
        utm_medium: e.utmMedium,
        utm_campaign: e.utmCampaign,
        is_bot: e.isBot,
      }],
    });
  }
}

export async function queryJson<T = unknown>(query: string, params: Record<string, unknown> = {}): Promise<T[]> {
  const result = await clickhouse.query({ query, query_params: params, format: 'JSONEachRow' });
  return await result.json<T[]>();
}
