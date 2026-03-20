-- Run this once to set up the database
-- psql -U postgres -d vidsearch -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    name        TEXT DEFAULT '',
    surname     TEXT DEFAULT '',
    avatar_url  TEXT DEFAULT '',
    subscription TEXT DEFAULT 'free',
    created_at  TIMESTAMPTZ DEFAULT now()
);
