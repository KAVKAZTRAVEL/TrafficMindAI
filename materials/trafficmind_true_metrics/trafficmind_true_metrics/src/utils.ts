import crypto from 'node:crypto';
import { nanoid } from 'nanoid';
import { UAParser } from 'ua-parser-js';
import type { Request } from 'express';
import { config } from './config.js';
import type { StoredEvent, TrackingEvent } from './types.js';

export function getClientIp(req: Request): string {
  const forwarded = req.headers['x-forwarded-for'];
  const raw = Array.isArray(forwarded) ? forwarded[0] : forwarded;
  return (raw?.split(',')[0] || req.socket.remoteAddress || '').trim();
}

export function hashIp(ip: string): string {
  return crypto.createHash('sha256').update(`${config.ipHashSalt}:${ip}`).digest('hex');
}

export function detectBot(userAgent: string): { isBot: 0 | 1; reason: string } {
  const ua = userAgent.toLowerCase();
  const hit = config.botUaDenylist.find((token) => ua.includes(token));
  if (hit) return { isBot: 1, reason: `ua:${hit}` };
  return { isBot: 0, reason: '' };
}

export function normalizeUrl(url?: string): { url: string; path: string } {
  if (!url) return { url: '', path: '' };
  try {
    const parsed = new URL(url);
    return { url: parsed.toString(), path: parsed.pathname || '/' };
  } catch {
    return { url, path: url.startsWith('/') ? url : '' };
  }
}

export function enrichEvent(input: TrackingEvent, req: Request): StoredEvent {
  const uaString = String(req.headers['user-agent'] || '');
  const ua = new UAParser(uaString).getResult();
  const ip = getClientIp(req);
  const bot = detectBot(uaString);
  const url = normalizeUrl(input.url);

  return {
    eventId: nanoid(21),
    eventTime: input.timestamp || new Date().toISOString(),
    receivedAt: new Date().toISOString(),

    projectId: input.projectId || 'default',
    siteId: input.siteId || 'default',
    event: input.event || 'event',
    visitorId: input.visitorId || 'anonymous',
    sessionId: input.sessionId || 'unknown',
    userId: input.userId || '',

    url: url.url,
    path: input.path || url.path,
    title: input.title || '',
    referrer: input.referrer || '',

    utmSource: input.utm?.source || '',
    utmMedium: input.utm?.medium || '',
    utmCampaign: input.utm?.campaign || '',
    utmContent: input.utm?.content || '',
    utmTerm: input.utm?.term || '',

    ipHash: hashIp(ip),
    userAgent: uaString,
    browser: ua.browser.name || '',
    os: ua.os.name || '',
    device: ua.device.type || 'desktop',
    country: String(req.headers['cf-ipcountry'] || ''),
    city: '',

    isBot: bot.isBot,
    botReason: bot.reason,
    source: input.source || 'browser',
    propertiesJson: JSON.stringify(input.properties || {}),
  };
}
