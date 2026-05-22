import { TrafficMindMetricsClient } from '../src/sdk.js';

const metrics = new TrafficMindMetricsClient({
  endpoint: process.env.TRUE_METRICS_ENDPOINT || 'http://localhost:8088',
  secret: process.env.COLLECTOR_SECRET || 'change_me_long_random_secret',
  projectId: 'trafficmind-ai',
  siteId: 'bot',
});

export async function onUserMessage(userId: string, text: string) {
  await metrics.track('bot_message_received', {
    userId,
    properties: {
      text_length: text.length,
      channel: 'telegram_or_web',
    },
  });

  // здесь вызывается твоя логика TrafficMind AI
}

export async function onLeadCreated(userId: string, source: string, value?: number) {
  await metrics.track('lead_created', {
    userId,
    properties: {
      source,
      value: value || 0,
    },
  });
}

export async function onReportGenerated(userId: string, reportType: string) {
  await metrics.track('report_generated', {
    userId,
    properties: {
      report_type: reportType,
    },
  });
}
