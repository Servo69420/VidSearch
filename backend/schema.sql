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

-- General table for videos (YouTube URLs and platform uploads)
CREATE TABLE IF NOT EXISTS yt_videos (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN ('upload', 'youtube')),
    source_url  TEXT UNIQUE NOT NULL,
    title       TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Private videos uploaded by users
CREATE TABLE IF NOT EXISTS user_videos (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name  TEXT NOT NULL,
    file_path  TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Transcriptions linked to either a shared video or a user video
CREATE TABLE IF NOT EXISTS transcriptions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id      UUID REFERENCES yt_videos(id) ON DELETE CASCADE,
    user_video_id UUID REFERENCES user_videos(id) ON DELETE CASCADE,
    full_text     TEXT NOT NULL,
    segments      JSONB NOT NULL,
    language      TEXT DEFAULT '',
    created_at    TIMESTAMPTZ DEFAULT now(),
    CHECK (
        (video_id IS NOT NULL AND user_video_id IS NULL) OR
        (video_id IS NULL AND user_video_id IS NOT NULL)
    )
);

-- Revoked JWT tokens (logout support)
CREATE TABLE IF NOT EXISTS token_blacklist (
    jti        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token      TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

-- chat history with reference to user and videos
CREATE TABLE IF NOT EXISTS chat_history (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id      UUID REFERENCES yt_videos(id) ON DELETE CASCADE,
    user_video_id UUID REFERENCES user_videos(id) ON DELETE CASCADE,
    role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content      TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now(),
    CHECK (
        (video_id IS NOT NULL AND user_video_id IS NULL) OR
        (video_id IS NULL AND user_video_id IS NOT NULL)
    )
);

