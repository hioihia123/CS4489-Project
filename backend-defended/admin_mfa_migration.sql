-- RUN AS A POSTGRESQL ADMINISTRATOR, CONNECTED TO defended_db ONLY.
SELECT current_database();

BEGIN;
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS totp_secret_enc TEXT,
    ADD COLUMN IF NOT EXISTS totp_last_used_step BIGINT;

-- Runtime application can read encrypted seeds (existing SELECT grant),
-- and only update replay-counter column, never alter enrollment secrets.
GRANT UPDATE (totp_last_used_step) ON public.users TO defended_app;
COMMIT;
