export type TrafficMindClientOptions = {
  endpoint: string;
  secret: string;
  projectId?: string;
  siteId?: string;
};

export class TrafficMindMetricsClient {
  constructor(private options: TrafficMindClientOptions) {}

  async track(event: string, data: {
    userId?: string;
    visitorId?: string;
    sessionId?: string;
    url?: string;
    referrer?: string;
    properties?: Record<string, unknown>;
  } = {}) {
    const res = await fetch(`${this.options.endpoint.replace(/\/$/, '')}/server-event`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${this.options.secret}`,
      },
      body: JSON.stringify({
        event,
        projectId: this.options.projectId || 'default',
        siteId: this.options.siteId || 'trafficmind-ai',
        userId: data.userId,
        visitorId: data.visitorId || data.userId || 'server',
        sessionId: data.sessionId || 'server',
        url: data.url,
        referrer: data.referrer,
        properties: data.properties || {},
      }),
    });

    if (!res.ok) {
      throw new Error(`TrafficMind metrics failed: ${res.status} ${await res.text()}`);
    }

    return res.json();
  }
}
