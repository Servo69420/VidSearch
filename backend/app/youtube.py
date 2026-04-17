from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

YOUTUBE_ID_SQL_EXPR = (
    "substring(source_url from "
    "'(?:v=|youtu\\.be/|shorts/)([A-Za-z0-9_-]{6,})')"
)


@dataclass(frozen=True)
class YouTubeRef:
    video_id: str
    canonical_url: str


@dataclass(frozen=True)
class ResolvedYouTubeVideo:
    yt_video_id: str
    ref: YouTubeRef


def extract_video_id(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()

    if not host and (
        candidate.startswith("youtube.com/")
        or candidate.startswith("www.youtube.com/")
        or candidate.startswith("m.youtube.com/")
        or candidate.startswith("music.youtube.com/")
        or candidate.startswith("youtu.be/")
        or candidate.startswith("www.youtu.be/")
    ):
        parsed = urlparse(f"https://{candidate}")
        host = (parsed.hostname or "").lower()

    if host in {"www.youtube.com", "youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/", 3)[2]
        return None

    if host in {"youtu.be", "www.youtu.be"}:
        return parsed.path.lstrip("/").split("/", 1)[0] or None

    # Allow plain YouTube IDs (tests and API callers often pass only the ID).
    if "/" not in candidate and "?" not in candidate and "&" not in candidate:
        if 6 <= len(candidate) <= 20:
            allowed = all(ch.isalnum() or ch in {"_", "-"} for ch in candidate)
            if allowed:
                return candidate

    return None


def canonical_video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def normalize_youtube_ref(value: str | None) -> YouTubeRef | None:
    video_id = extract_video_id(value)
    if not video_id:
        return None
    return YouTubeRef(video_id=video_id, canonical_url=canonical_video_url(video_id))


async def resolve_or_create_yt_video(db, value: str) -> ResolvedYouTubeVideo:
    ref = normalize_youtube_ref(value)
    if not ref:
        raise ValueError("Invalid YouTube URL")

    row = await db.fetchrow(
        f"""SELECT id, source_url
            FROM yt_videos
            WHERE source_url = $1 OR {YOUTUBE_ID_SQL_EXPR} = $2
            ORDER BY (source_url = $1) DESC, created_at ASC
            LIMIT 1""",
        ref.canonical_url,
        ref.video_id,
    )

    if row:
        if row["source_url"] != ref.canonical_url:
            await db.execute(
                """UPDATE yt_videos AS target
                   SET source_url = $1
                   WHERE target.id = $2
                     AND NOT EXISTS (
                         SELECT 1
                         FROM yt_videos other
                         WHERE other.source_url = $1 AND other.id <> target.id
                     )""",
                ref.canonical_url,
                row["id"],
            )
        return ResolvedYouTubeVideo(yt_video_id=str(row["id"]), ref=ref)

    created_id = await db.fetchval(
        """INSERT INTO yt_videos (source_type, source_url)
           VALUES ('youtube', $1)
           ON CONFLICT (source_url)
           DO UPDATE SET source_url = EXCLUDED.source_url
           RETURNING id""",
        ref.canonical_url,
    )
    return ResolvedYouTubeVideo(yt_video_id=str(created_id), ref=ref)
