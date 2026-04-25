"""Unit tests for admin CSV exporters and TXT URL importer."""

import csv
import io
import unittest
from datetime import datetime, timezone

from app.routers.admin import (
    StatsExporter,
    TranscriptionsExporter,
    VideosExporter,
    TXTURLImporter,
)


def _parse_csv(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def _stats_rec(**overrides):
    base = {
        "username": "alice",
        "email": "alice@example.com",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "subscription": "free",
        "transcriptions": 3,
        "uploaded_videos": 1,
        "chat_messages": 10,
        "total_chars": 5 * 130 * 2,  # → 2 minutes
    }
    return {**base, **overrides}


def _transcript_rec(**overrides):
    base = {
        "title": "My Video",
        "source_type": "youtube",
        "source_url": "https://youtu.be/abc",
        "language": "en",
        "status": "ready",
        "model_version": "whisper-1",
        "created_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
        "char_count": 1300,
        "username": "bob",
    }
    return {**base, **overrides}


def _yt_video_rec(**overrides):
    base = {
        "title": "YT Video",
        "source_type": "youtube",
        "source_url": "https://youtu.be/xyz",
        "created_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
        "transcription_status": "ready",
        "language": "en",
    }
    return {**base, **overrides}


def _upload_rec(**overrides):
    base = {
        "title": "upload.mp4",
        "source_type": "upload",
        "source_url": "",
        "created_at": datetime(2026, 2, 2, tzinfo=timezone.utc),
        "transcription_status": "pending",
        "language": None,
        "username": "charlie",
    }
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# StatsExporter
# ---------------------------------------------------------------------------

class TestStatsExporter(unittest.TestCase):
    def setUp(self):
        self._exp = StatsExporter()

    def test_fieldnames_count(self):
        self.assertEqual(len(self._exp.fieldnames), 9)

    def test_export_header_row(self):
        rows = _parse_csv(self._exp.export([]))
        self.assertEqual(rows[0][0], "username")

    def test_export_data_row(self):
        rows = _parse_csv(self._exp.export([_stats_rec()]))
        self.assertEqual(rows[1][0], "alice")
        self.assertEqual(rows[1][1], "alice@example.com")

    def test_est_minutes_calculated(self):
        rows = _parse_csv(self._exp.export([_stats_rec()]))
        self.assertEqual(float(rows[1][7]), 2.0)

    def test_none_email_becomes_empty_string(self):
        rows = _parse_csv(self._exp.export([_stats_rec(email=None)]))
        self.assertEqual(rows[1][1], "")

    def test_empty_records_only_header(self):
        rows = _parse_csv(self._exp.export([]))
        self.assertEqual(len(rows), 1)


# ---------------------------------------------------------------------------
# TranscriptionsExporter
# ---------------------------------------------------------------------------

class TestTranscriptionsExporter(unittest.TestCase):
    def setUp(self):
        self._exp = TranscriptionsExporter()

    def test_fieldnames_count(self):
        self.assertEqual(len(self._exp.fieldnames), 10)

    def test_word_count_derived_from_char_count(self):
        rows = _parse_csv(self._exp.export([_transcript_rec()]))
        self.assertEqual(int(rows[1][7]), 260)  # 1300 // 5

    def test_none_language_becomes_empty(self):
        rows = _parse_csv(self._exp.export([_transcript_rec(language=None)]))
        self.assertEqual(rows[1][3], "")

    def test_none_created_at_becomes_empty(self):
        rows = _parse_csv(self._exp.export([_transcript_rec(created_at=None)]))
        self.assertEqual(rows[1][6], "")


# ---------------------------------------------------------------------------
# VideosExporter
# ---------------------------------------------------------------------------

class TestVideosExporter(unittest.TestCase):
    def setUp(self):
        self._exp = VideosExporter()

    def test_fieldnames_count(self):
        self.assertEqual(len(self._exp.fieldnames), 7)

    def test_yt_row_has_empty_uploaded_by(self):
        rows = _parse_csv(self._exp.export([_yt_video_rec()]))
        self.assertEqual(rows[1][6], "")

    def test_upload_row_has_username(self):
        rows = _parse_csv(self._exp.export([_upload_rec()]))
        self.assertEqual(rows[1][6], "charlie")

    def test_mixed_records(self):
        rows = _parse_csv(self._exp.export([_yt_video_rec(), _upload_rec()]))
        self.assertEqual(len(rows), 3)  # header + 2 data rows


# ---------------------------------------------------------------------------
# TXTURLImporter
# ---------------------------------------------------------------------------

class TestTXTURLImporter(unittest.TestCase):
    def setUp(self):
        self._imp = TXTURLImporter()

    def test_parses_single_url(self):
        result = self._imp.parse("https://youtu.be/abc123\n")
        self.assertEqual(result, ["https://youtu.be/abc123"])

    def test_skips_blank_lines(self):
        result = self._imp.parse("\nhttps://youtu.be/a\n\nhttps://youtu.be/b\n")
        self.assertEqual(len(result), 2)

    def test_skips_comment_lines(self):
        result = self._imp.parse("# comment\nhttps://youtu.be/abc\n")
        self.assertEqual(result, ["https://youtu.be/abc"])

    def test_empty_content_returns_empty_list(self):
        self.assertEqual(self._imp.parse(""), [])

    def test_strips_whitespace_from_urls(self):
        result = self._imp.parse("  https://youtu.be/abc  \n")
        self.assertEqual(result[0], "https://youtu.be/abc")

    def test_multiple_comments_and_blanks(self):
        content = "# batch 1\nhttps://youtu.be/x\n\n# batch 2\nhttps://youtu.be/y\n"
        result = self._imp.parse(content)
        self.assertEqual(len(result), 2)

    def test_inheritance_is_base(self):
        from app.routers.admin import BaseCSVExporter
        self.assertIsInstance(StatsExporter(), BaseCSVExporter)
        self.assertIsInstance(TranscriptionsExporter(), BaseCSVExporter)
        self.assertIsInstance(VideosExporter(), BaseCSVExporter)


if __name__ == "__main__":
    unittest.main()
