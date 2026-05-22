CREATE DATABASE IF NOT EXISTS trafficmind;

CREATE TABLE IF NOT EXISTS trafficmind.events
(
    event_id String,
    event_time DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    project_id LowCardinality(String),
    site_id LowCardinality(String),
    event_name LowCardinality(String),

    visitor_id String,
    session_id String,
    user_id String,

    url String,
    path String,
    title String,
    referrer String,
    utm_source String,
    utm_medium String,
    utm_campaign String,
    utm_content String,
    utm_term String,

    ip_hash String,
    user_agent String,
    browser LowCardinality(String),
    os LowCardinality(String),
    device LowCardinality(String),
    country LowCardinality(String),
    city LowCardinality(String),

    is_bot UInt8,
    bot_reason String,
    source LowCardinality(String),
    properties String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (project_id, site_id, event_time, visitor_id, session_id, event_name);

CREATE TABLE IF NOT EXISTS trafficmind.pageviews
(
    event_time DateTime64(3, 'UTC'),
    project_id LowCardinality(String),
    site_id LowCardinality(String),
    visitor_id String,
    session_id String,
    url String,
    path String,
    referrer String,
    utm_source String,
    utm_medium String,
    utm_campaign String,
    is_bot UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (project_id, site_id, event_time, path);
