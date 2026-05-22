import { config } from './config.js';
import type { StoredEvent } from './types.js';

export async function forwardToPostHog(e: StoredEvent): Promise<void> {
  if (!config.posthog.enabled || !config.posthog.host || !config.posthog.projectApiKey) return;

  const endpoint = `${config.posthog.host.replace(/\/$/, '')}/i/v0/e/`;

  const payload = {
    api_key: config.posthog.projectApiKey,
    event: e.event,
    distinct_id: e.userId || e.visitorId,
    timestamp: e.eventTime,
    properties: {
      $current_url: e.url,
      $referrer: e.referrer,
      $browser: e.browser,
      $os: e.os,
      $device_type: e.device,
      tm_project_id: e.projectId,
      tm_site_id: e.siteId,
      tm_session_id: e.sessionId,
      tm_event_id: e.eventId,
      tm_source: e.source,
      tm_is_bot: Boolean(e.isBot),
      tm_bot_reason: e.botReason,
      tm_utm_source: e.utmSource,
      tm_utm_medium: e.utmMedium,
      tm_utm_campaign: e.utmCampaign,
      ...safeJson(e.propertiesJson),
    },
  };

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`PostHog forwarding failed: ${res.status} ${text}`);
  }
}

function safeJson(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}
