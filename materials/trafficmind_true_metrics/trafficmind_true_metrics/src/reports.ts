import { Router } from 'express';
import { queryJson } from './clickhouse.js';
import { config } from './config.js';

export const reportsRouter = Router();

function requireSecret(req: any, res: any, next: any) {
  const token = req.headers.authorization?.replace(/^Bearer\s+/i, '');
  if (token !== config.collectorSecret) {
    return res.status(401).json({ ok: false, error: 'unauthorized' });
  }
  next();
}

reportsRouter.use(requireSecret);

reportsRouter.get('/summary', async (req, res, next) => {
  try {
    const projectId = String(req.query.projectId || 'default');
    const days = Number(req.query.days || 7);

    const rows = await queryJson(`
      SELECT
        count() AS events,
        uniqExact(visitor_id) AS visitors,
        uniqExact(session_id) AS sessions,
        countIf(event_name = 'pageview') AS pageviews,
        round(100 * countIf(is_bot = 1) / greatest(count(), 1), 2) AS bot_percent,
        round(100 * countIf(source = 'server') / greatest(count(), 1), 2) AS server_side_percent
      FROM events
      WHERE project_id = {projectId:String}
        AND event_time >= now() - INTERVAL {days:UInt32} DAY
    `, { projectId, days });

    res.json({ ok: true, projectId, days, data: rows[0] || {} });
  } catch (err) {
    next(err);
  }
});

reportsRouter.get('/sources', async (req, res, next) => {
  try {
    const projectId = String(req.query.projectId || 'default');
    const days = Number(req.query.days || 7);
    const rows = await queryJson(`
      SELECT
        if(utm_source != '', utm_source, if(referrer = '', 'direct', referrer)) AS source,
        count() AS events,
        uniqExact(visitor_id) AS visitors,
        uniqExact(session_id) AS sessions
      FROM events
      WHERE project_id = {projectId:String}
        AND event_time >= now() - INTERVAL {days:UInt32} DAY
        AND is_bot = 0
      GROUP BY source
      ORDER BY visitors DESC
      LIMIT 50
    `, { projectId, days });
    res.json({ ok: true, data: rows });
  } catch (err) {
    next(err);
  }
});

reportsRouter.get('/pages', async (req, res, next) => {
  try {
    const projectId = String(req.query.projectId || 'default');
    const days = Number(req.query.days || 7);
    const rows = await queryJson(`
      SELECT
        path,
        count() AS pageviews,
        uniqExact(visitor_id) AS visitors,
        uniqExact(session_id) AS sessions
      FROM pageviews
      WHERE project_id = {projectId:String}
        AND event_time >= now() - INTERVAL {days:UInt32} DAY
        AND is_bot = 0
      GROUP BY path
      ORDER BY pageviews DESC
      LIMIT 100
    `, { projectId, days });
    res.json({ ok: true, data: rows });
  } catch (err) {
    next(err);
  }
});

reportsRouter.get('/truth-score', async (req, res, next) => {
  try {
    const projectId = String(req.query.projectId || 'default');
    const days = Number(req.query.days || 7);
    const rows = await queryJson(`
      SELECT
        count() AS total_events,
        countIf(is_bot = 1) AS bot_events,
        countIf(source = 'server') AS server_events,
        countIf(source = 'browser') AS browser_events,
        round(100 - (100 * countIf(is_bot = 1) / greatest(count(), 1)), 2) AS clean_traffic_percent,
        round(100 * countIf(source = 'server') / greatest(count(), 1), 2) AS server_verified_percent
      FROM events
      WHERE project_id = {projectId:String}
        AND event_time >= now() - INTERVAL {days:UInt32} DAY
    `, { projectId, days });
    res.json({
      ok: true,
      data: rows[0] || {},
      explanation: 'clean_traffic_percent excludes detected bots; server_verified_percent shows how much data came from trusted backend/server events.',
    });
  } catch (err) {
    next(err);
  }
});
