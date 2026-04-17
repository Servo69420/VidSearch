"""Tests for YouTubeTranscriber URL parsing and TranscriberFactory.

The whisper model is heavy and loads at import time inside
TranscriberFactory, so we mock it before importing.

Run:  python -m unittest tests.test_transcription -v
"""

import sys
import unittest
from unittest.mock import MagicMock

# --- Mock whisper BEFORE importing app.transcription ---
# VideoFileTranscriber.__init__ calls whisper.load_model() at class level
# inside TranscriberFactory, which would fail without a GPU / model files.
mock_whisper = MagicMock()
sys.modules["whisper"] = mock_whisper
sys.modules["youtube_transcript_api"] = MagicMock()
sys.modules["ffmpeg"] = MagicMock()

from app.transcription import (  # noqa: E402
    TranscriberFactory,
    YouTubeTranscriber,
    VideoFileTranscriber,
)


class TestYouTubeURLParsing(unittest.TestCase):
    """Test the private __get_video_id method via name-mangling."""

    def setUp(self):
        self.yt = YouTubeTranscriber()

    def _parse(self, url: str) -> str | None:
        # Access name-mangled private method
        return self.yt._YouTubeTranscriber__get_video_id(url)

    def test_standard_youtube_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(self._parse(url), "dQw4w9WgXcQ")

    def test_youtube_without_www(self):
        url = "https://youtube.com/watch?v=abc123XYZ_-"
        self.assertEqual(self._parse(url), "abc123XYZ_-")

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(self._parse(url), "dQw4w9WgXcQ")

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=abc123&t=120&list=PLxyz"
        self.assertEqual(self._parse(url), "abc123")

    def test_invalid_url_returns_none(self):
        self.assertIsNone(self._parse("https://vimeo.com/12345"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self._parse(""))

    def test_random_text_returns_none(self):
        self.assertIsNone(self._parse("not a url at all"))

    def test_youtube_url_missing_v_param(self):
        url = "https://www.youtube.com/watch?list=PLxyz"
        self.assertIsNone(self._parse(url))


class TestTranscriberFactory(unittest.TestCase):
    """Factory returns the correct transcriber subclass."""

    def test_youtube_com_returns_yt_transcriber(self):
        t = TranscriberFactory.get_transcriber(
            "https://www.youtube.com/watch?v=abc"
        )
        self.assertIsInstance(t, YouTubeTranscriber)

    def test_youtu_be_returns_yt_transcriber(self):
        t = TranscriberFactory.get_transcriber("https://youtu.be/abc")
        self.assertIsInstance(t, YouTubeTranscriber)

    def test_plain_youtube_id_returns_yt_transcriber(self):
        t = TranscriberFactory.get_transcriber("dQw4w9WgXcQ")
        self.assertIsInstance(t, YouTubeTranscriber)

    def test_file_path_returns_video_transcriber(self):
        t = TranscriberFactory.get_transcriber("/home/user/video.mp4")
        self.assertIsInstance(t, VideoFileTranscriber)

    def test_random_string_returns_video_transcriber(self):
        t = TranscriberFactory.get_transcriber("some-random-path.mkv")
        self.assertIsInstance(t, VideoFileTranscriber)

    def test_factory_returns_singletons(self):
        """Factory reuses the same instance — not creating new objects."""
        t1 = TranscriberFactory.get_transcriber("https://youtube.com/watch?v=a")
        t2 = TranscriberFactory.get_transcriber("https://youtube.com/watch?v=b")
        self.assertIs(t1, t2)


class TestTranscriberInheritance(unittest.TestCase):
    """Verify the OOP hierarchy — useful for the coursework report."""

    def test_youtube_transcriber_is_base(self):
        from app.transcription import BaseTranscriber
        self.assertTrue(issubclass(YouTubeTranscriber, BaseTranscriber))

    def test_video_file_transcriber_is_base(self):
        from app.transcription import BaseTranscriber
        self.assertTrue(issubclass(VideoFileTranscriber, BaseTranscriber))

    def test_base_cannot_be_instantiated(self):
        from app.transcription import BaseTranscriber
        with self.assertRaises(TypeError):
            BaseTranscriber()


if __name__ == "__main__":
    unittest.main()
