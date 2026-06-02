import logging

import bcrypt

from app.embedder import DEFAULT_EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)


async def ensure_embedding_dimensions(db) -> None:
    expected_type = f"vector({DEFAULT_EMBEDDING_DIMENSIONS})"
    rows = await db.fetch(
        """
        SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS column_type
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname = 'transcript_chunks'
          AND a.attname IN ('embedding', 'summary_embedding')
          AND NOT a.attisdropped
        """
    )

    column_types = {row["attname"]: row["column_type"] for row in rows}
    if (
        column_types.get("embedding") == expected_type
        and column_types.get("summary_embedding") == expected_type
    ):
        return

    logger.warning(
        "Migrating transcript_chunks vector columns to %s; existing chunks "
        "will be rebuilt when videos are transcribed again.",
        expected_type,
    )
    await db.execute(
        f"""
        DROP INDEX IF EXISTS transcript_chunks_embedding_idx;
        DROP INDEX IF EXISTS transcript_chunks_summary_embedding_idx;
        DELETE FROM transcript_chunks;
        UPDATE transcriptions
        SET status = 'pending'
        WHERE video_id IS NOT NULL AND status = 'ready';
        ALTER TABLE transcript_chunks
            ALTER COLUMN embedding TYPE vector({DEFAULT_EMBEDDING_DIMENSIONS}),
            ALTER COLUMN summary_embedding TYPE vector({DEFAULT_EMBEDDING_DIMENSIONS});
        CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_idx
            ON transcript_chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        CREATE INDEX IF NOT EXISTS transcript_chunks_summary_embedding_idx
            ON transcript_chunks USING ivfflat (summary_embedding vector_cosine_ops)
            WITH (lists = 100);
        """
    )


async def ensure_frame_captures(db) -> None:
    """Create the frame-analysis cache table (idempotent).

    Brings existing deployments forward without dropping data: the table is
    created if missing, and the cache columns are added if an older
    frame_captures table already exists.
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS frame_captures (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            video_key      TEXT NOT NULL,
            timestamp_s    REAL NOT NULL DEFAULT 0,
            analysis       TEXT,
            analysis_model TEXT,
            analyzed_at    TIMESTAMPTZ,
            ask_count      INT NOT NULL DEFAULT 0,
            last_asked_at  TIMESTAMPTZ,
            created_at     TIMESTAMPTZ DEFAULT now()
        );
        ALTER TABLE frame_captures
            ADD COLUMN IF NOT EXISTS analysis       TEXT,
            ADD COLUMN IF NOT EXISTS analysis_model TEXT,
            ADD COLUMN IF NOT EXISTS analyzed_at    TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS ask_count      INT NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_asked_at  TIMESTAMPTZ;
        CREATE INDEX IF NOT EXISTS frame_captures_user_video_ts_idx
            ON frame_captures (user_id, video_key, timestamp_s);
        """
    )


async def ensure_admin_setup(db) -> None:
    """Add is_admin column and create the default admin account."""
    await db.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"
    )

    exists = await db.fetchval("SELECT 1 FROM users WHERE username = 'admin'")
    if not exists:
        hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
        await db.execute(
            "INSERT INTO users (username, password_hash, is_admin) "
            "VALUES ('admin', $1, TRUE)",
            hashed,
        )
        logger.info("Admin account created (username=admin, default password=admin)")
    else:
        await db.execute(
            "UPDATE users SET is_admin = TRUE WHERE username = 'admin' AND is_admin = FALSE"
        )
