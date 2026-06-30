import logging

from app.embedder import DEFAULT_EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)


async def ensure_barebones_schema(db) -> None:
    """Remove obsolete account/session database objects from existing volumes."""
    await db.execute(
        """
        ALTER TABLE IF EXISTS user_videos
            DROP CONSTRAINT IF EXISTS user_videos_user_id_fkey;
        ALTER TABLE IF EXISTS chat_history
            DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey;
        ALTER TABLE IF EXISTS user_videos
            DROP COLUMN IF EXISTS user_id;
        ALTER TABLE IF EXISTS chat_history
            DROP COLUMN IF EXISTS user_id;
        DROP TABLE IF EXISTS token_blacklist CASCADE;
        DROP TABLE IF EXISTS user_hobbies CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        """
    )


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

