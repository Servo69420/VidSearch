-- Run this once to set up the database
-- psql -U postgres -d vidsearch -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    name          TEXT DEFAULT '',
    surname       TEXT DEFAULT '',
    avatar_url    TEXT DEFAULT '',
    subscription  TEXT DEFAULT 'free',
    created_at    TIMESTAMPTZ DEFAULT now(),
    hobbies       TEXT[] DEFAULT '{}'
);

-- Shared videos: platform videos and YouTube URLs (deduplicated by source_url)
CREATE TABLE IF NOT EXISTS videos (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN ('platform', 'url')),
    source_url  TEXT UNIQUE NOT NULL,
    title       TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Private videos uploaded by users
CREATE TABLE IF NOT EXISTS user_videos (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_path         TEXT NOT NULL,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- Transcriptions linked to either a shared video or a user video
CREATE TABLE IF NOT EXISTS transcriptions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id      UUID REFERENCES videos(id) ON DELETE CASCADE,
    user_video_id UUID REFERENCES user_videos(id) ON DELETE CASCADE,
    full_text     TEXT NOT NULL,
    segments      JSONB,
    language      TEXT DEFAULT '',
    created_at    TIMESTAMPTZ DEFAULT now(),
    CHECK (
        (video_id IS NOT NULL AND user_video_id IS NULL) OR
        (video_id IS NULL AND user_video_id IS NOT NULL)
    )
);
