import { z } from 'zod';

export const trackingEventSchema = z.object({
  event: z.string().min(1).max(120).default('event'),
  projectId: z.string().min(1).max(80).default('default'),
  siteId: z.string().min(1).max(80).default('default'),
  visitorId: z.string().min(1).max(160).optional(),
  sessionId: z.string().min(1).max(160).optional(),
  userId: z.string().max(160).optional(),
  url: z.string().max(3000).optional(),
  path: z.string().max(1000).optional(),
  title: z.string().max(500).optional(),
  referrer: z.string().max(3000).optional(),
  utm: z.object({
    source: z.string().max(300).optional(),
    medium: z.string().max(300).optional(),
    campaign: z.string().max(300).optional(),
    content: z.string().max(300).optional(),
    term: z.string().max(300).optional(),
  }).optional(),
  properties: z.record(z.unknown()).optional(),
  timestamp: z.string().datetime().optional(),
  source: z.enum(['browser', 'server', 'bot', 'import']).optional(),
});
