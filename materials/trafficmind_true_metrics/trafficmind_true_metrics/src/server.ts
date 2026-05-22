import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from './config.js';
import { enrichEvent } from './utils.js';
import { insertEvent } from './clickhouse.js';
import { forwardToPostHog } from './posthog.js';
import { trackingEventSchema } from './validation.js';
import { reportsRouter } from './reports.js';

const app = express();
const __dirname = path.dirname(fileURLToPath(import.meta.url));

app.use(helmet({ crossOriginResourcePolicy: false }));
app.use(cors({ origin: config.publicTrackingOrigin === '*' ? true : config.publicTrackingOrigin }));
app.use(express.json({ limit: '128kb' }));

app.get('/health', (_req, res) => res.json({ ok: true, service: 'trafficmind-true-metrics' }));

app.use('/static', express.static(path.join(__dirname, '..', 'public'), {
  maxAge: '1h',
  etag: true,
}));

app.post('/collect', async (req, res, next) => {
  try {
    const parsed = trackingEventSchema.parse(req.body);
    const event = enrichEvent(parsed, req);

    await insertEvent(event);

    forwardToPostHog(event).catch((err) => {
      console.error('[posthog-forward-error]', err.message);
    });

    res.status(202).json({ ok: true, eventId: event.eventId });
  } catch (err) {
    next(err);
  }
});

app.post('/server-event', async (req, res, next) => {
  try {
    const token = req.headers.authorization?.replace(/^Bearer\s+/i, '');
    if (token !== config.collectorSecret) {
      return res.status(401).json({ ok: false, error: 'unauthorized' });
    }

    const parsed = trackingEventSchema.parse({ ...req.body, source: 'server' });
    const event = enrichEvent(parsed, req);

    await insertEvent(event);
    await forwardToPostHog(event).catch((err) => {
      console.error('[posthog-forward-error]', err.message);
    });

    res.status(202).json({ ok: true, eventId: event.eventId });
  } catch (err) {
    next(err);
  }
});

app.use('/reports', reportsRouter);

app.use((err: any, _req: any, res: any, _next: any) => {
  console.error(err);
  res.status(400).json({ ok: false, error: err?.message || 'bad_request' });
});

app.listen(config.port, () => {
  console.log(`TrafficMind TrueMetrics collector running on :${config.port}`);
});
