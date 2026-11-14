-- Run ONCE as the PostgreSQL administrator while connected to defended_db.
-- Do NOT run against vulnerable_db.
CREATE TABLE IF NOT EXISTS login_rate_limits (
    scope TEXT NOT NULL CHECK (scope IN ('account', 'ip')),
    subject_hash CHAR(64) NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    window_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope, subject_hash)
);

GRANT USAGE ON SCHEMA public TO defended_app;
GRANT SELECT, INSERT, UPDATE ON login_rate_limits TO defended_app;
