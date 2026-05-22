export type TrackingEvent = {
  event?: string;
  projectId?: string;
  siteId?: string;
  visitorId?: string;
  sessionId?: string;
  userId?: string;
  url?: string;
  path?: string;
  title?: string;
  referrer?: string;
  utm?: {
    source?: string;
    medium?: string;
    campaign?: string;
    content?: string;
    term?: string;
  };
  properties?: Record<string, unknown>;
  timestamp?: string;
  source?: 'browser' | 'server' | 'bot' | 'import';
};

export type StoredEvent = Required<Omit<TrackingEvent, 'utm' | 'properties' | 'timestamp'>> & {
  eventId: string;
  eventTime: string;
  receivedAt: string;
  utmSource: string;
  utmMedium: string;
  utmCampaign: string;
  utmContent: string;
  utmTerm: string;
  ipHash: string;
  userAgent: string;
  browser: string;
  os: string;
  device: string;
  country: string;
  city: string;
  isBot: 0 | 1;
  botReason: string;
  propertiesJson: string;
};
