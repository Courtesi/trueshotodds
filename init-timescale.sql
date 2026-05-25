CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS line_movements (
    time         TIMESTAMPTZ NOT NULL,
    league       TEXT        NOT NULL,
    event_id     TEXT        NOT NULL,
    market_type  TEXT        NOT NULL,
    outcome_name TEXT        NOT NULL,
    sportsbook   TEXT        NOT NULL,
    odds         FLOAT8      NOT NULL
);

SELECT create_hypertable('line_movements', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_line_movements_event_time
    ON line_movements (event_id, time DESC);

ALTER TABLE line_movements SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'event_id,outcome_name,sportsbook',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('line_movements', INTERVAL '2 hours', if_not_exists => TRUE);
SELECT add_retention_policy('line_movements', INTERVAL '24 hours', if_not_exists => TRUE);