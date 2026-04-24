"""Admin router — statistics and CSV export endpoints."""

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


async def require_admin(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    is_admin = await db.fetchval(
        "SELECT is_admin FROM users WHERE id = $1::uuid",
        current_user["sub"],
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/stats")
async def get_stats(_admin=Depends(require_admin), db=Depends(get_db)):
    total_users = await db.fetchval("SELECT COUNT(*) FROM users")
    new_users_7d = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE created_at > now() - interval '7 days'"
    )
    new_users_30d = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE created_at > now() - interval '30 days'"
    )
    users_by_sub = await db.fetch(
        "SELECT subscription, COUNT(*) AS count FROM users "
        "GROUP BY subscription ORDER BY count DESC"
    )

    total_transcriptions = await db.fetchval("SELECT COUNT(*) FROM transcriptions")
    yt_transcriptions = await db.fetchval(
        "SELECT COUNT(*) FROM transcriptions WHERE video_id IS NOT NULL"
    )
    upload_transcriptions = await db.fetchval(
        "SELECT COUNT(*) FROM transcriptions WHERE user_video_id IS NOT NULL"
    )
    by_status = await db.fetch(
        "SELECT status, COUNT(*) AS count FROM transcriptions "
        "GROUP BY status ORDER BY count DESC"
    )
    total_chars = await db.fetchval(
        "SELECT COALESCE(SUM(length(full_text)), 0) FROM transcriptions "
        "WHERE status = 'ready'"
    )
    est_words = (total_chars or 0) / 5
    est_minutes = est_words / 130
    est_cost = round(est_minutes * 0.006, 4)

    total_yt_videos = await db.fetchval("SELECT COUNT(*) FROM yt_videos")
    total_user_videos = await db.fetchval("SELECT COUNT(*) FROM user_videos")

    total_messages = await db.fetchval("SELECT COUNT(*) FROM chat_history")
    user_questions = await db.fetchval(
        "SELECT COUNT(*) FROM chat_history WHERE role = 'user'"
    )
    chat_sessions = await db.fetchval(
        "SELECT COUNT(*) FROM ("
        "  SELECT DISTINCT user_id, COALESCE(video_id::text, user_video_id::text)"
        "  FROM chat_history"
        ") sub"
    )

    return {
        "users": {
            "total": total_users,
            "new_last_7_days": new_users_7d,
            "new_last_30_days": new_users_30d,
            "by_subscription": [dict(r) for r in users_by_sub],
        },
        "transcriptions": {
            "total": total_transcriptions,
            "youtube": yt_transcriptions,
            "uploaded": upload_transcriptions,
            "by_status": [dict(r) for r in by_status],
            "est_minutes": round(est_minutes, 1),
            "est_cost_usd": est_cost,
        },
        "videos": {
            "youtube_videos": total_yt_videos,
            "user_uploaded": total_user_videos,
            "total": (total_yt_videos or 0) + (total_user_videos or 0),
        },
        "chat": {
            "total_messages": total_messages,
            "user_questions": user_questions,
            "chat_sessions": chat_sessions,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats/export.csv")
async def export_stats_csv(_admin=Depends(require_admin), db=Depends(get_db)):
    rows = await db.fetch(
        """
        SELECT
            u.username,
            u.email,
            u.created_at,
            u.subscription,
            -- upload transcriptions (owned by this user)
            (
                SELECT COUNT(DISTINCT t.id)
                FROM user_videos uv
                JOIN transcriptions t ON t.user_video_id = uv.id
                WHERE uv.user_id = u.id
            ) +
            -- YouTube transcriptions this user has chatted about
            (
                SELECT COUNT(DISTINCT t.id)
                FROM chat_history ch
                JOIN transcriptions t ON t.video_id = ch.video_id
                WHERE ch.user_id = u.id AND ch.video_id IS NOT NULL
            ) AS transcriptions,
            (SELECT COUNT(*) FROM user_videos WHERE user_id = u.id) AS uploaded_videos,
            (SELECT COUNT(*) FROM chat_history WHERE user_id = u.id) AS chat_messages,
            -- cost estimate: only uploaded transcripts are "owned" costs
            COALESCE((
                SELECT SUM(length(t.full_text))
                FROM user_videos uv
                JOIN transcriptions t ON t.user_video_id = uv.id
                WHERE uv.user_id = u.id
            ), 0) AS total_chars
        FROM users u
        ORDER BY u.created_at
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "username", "email", "joined_at", "subscription",
        "transcriptions", "uploaded_videos", "chat_messages",
        "est_transcription_minutes", "est_transcription_cost_usd",
    ])
    for r in rows:
        est_min = round((r["total_chars"] / 5) / 130, 2)
        est_cost = round(est_min * 0.006, 4)
        writer.writerow([
            r["username"],
            r["email"] or "",
            r["created_at"].isoformat() if r["created_at"] else "",
            r["subscription"] or "free",
            r["transcriptions"],
            r["uploaded_videos"],
            r["chat_messages"],
            est_min,
            est_cost,
        ])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"vidsearch_stats_{ts}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/transcriptions/export.csv")
async def export_transcriptions_csv(_admin=Depends(require_admin), db=Depends(get_db)):
    rows = await db.fetch(
        """
        SELECT
            COALESCE(yv.title, uv.file_name, 'Unknown') AS title,
            COALESCE(yv.source_type, 'upload')          AS source_type,
            COALESCE(yv.source_url, '')                 AS source_url,
            t.language,
            t.status,
            t.model_version,
            t.created_at,
            COALESCE(length(t.full_text), 0)            AS char_count,
            u.username
        FROM transcriptions t
        LEFT JOIN yt_videos yv   ON yv.id = t.video_id
        LEFT JOIN user_videos uv ON uv.id = t.user_video_id
        LEFT JOIN users u        ON u.id = uv.user_id
        ORDER BY t.created_at
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "title", "source_type", "source_url", "language", "status",
        "model_version", "created_at", "word_count", "est_minutes", "username",
    ])
    for r in rows:
        word_count = r["char_count"] // 5
        est_min = round(word_count / 130, 2)
        writer.writerow([
            r["title"],
            r["source_type"],
            r["source_url"],
            r["language"] or "",
            r["status"],
            r["model_version"] or "",
            r["created_at"].isoformat() if r["created_at"] else "",
            word_count,
            est_min,
            r["username"] or "",
        ])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"vidsearch_transcriptions_{ts}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/videos/export.csv")
async def export_videos_csv(_admin=Depends(require_admin), db=Depends(get_db)):
    yt_rows = await db.fetch(
        """
        SELECT
            yv.title,
            'youtube'       AS source_type,
            yv.source_url,
            yv.created_at,
            t.status        AS transcription_status,
            t.language
        FROM yt_videos yv
        LEFT JOIN transcriptions t ON t.video_id = yv.id
        ORDER BY yv.created_at
        """
    )
    upload_rows = await db.fetch(
        """
        SELECT
            uv.file_name    AS title,
            'upload'        AS source_type,
            ''              AS source_url,
            uv.created_at,
            t.status        AS transcription_status,
            t.language,
            u.username
        FROM user_videos uv
        JOIN users u ON u.id = uv.user_id
        LEFT JOIN transcriptions t ON t.user_video_id = uv.id
        ORDER BY uv.created_at
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "title", "source_type", "source_url", "created_at",
        "transcription_status", "language", "uploaded_by",
    ])
    for r in yt_rows:
        writer.writerow([
            r["title"] or "",
            r["source_type"],
            r["source_url"] or "",
            r["created_at"].isoformat() if r["created_at"] else "",
            r["transcription_status"] or "none",
            r["language"] or "",
            "",
        ])
    for r in upload_rows:
        writer.writerow([
            r["title"] or "",
            r["source_type"],
            r["source_url"],
            r["created_at"].isoformat() if r["created_at"] else "",
            r["transcription_status"] or "none",
            r["language"] or "",
            r["username"] or "",
        ])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"vidsearch_videos_{ts}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
