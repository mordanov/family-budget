-- Family Budget DB initialization
-- This file is mounted as docker-entrypoint-initdb.d and runs only on first DB creation.
-- Actual schema is managed by Alembic migrations.
-- This file just ensures the DB and extensions exist.

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';
