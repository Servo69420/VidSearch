import unittest

from app.youtube import canonical_video_url, extract_video_id, normalize_youtube_ref


class TestYouTubeUtils(unittest.TestCase):
    def test_extract_from_watch_url(self):
        value = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=12"
        self.assertEqual(extract_video_id(value), "dQw4w9WgXcQ")

    def test_extract_from_short_url(self):
        value = "https://youtu.be/dQw4w9WgXcQ?si=123"
        self.assertEqual(extract_video_id(value), "dQw4w9WgXcQ")

    def test_extract_from_shorts_url(self):
        value = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(value), "dQw4w9WgXcQ")

    def test_extract_from_url_without_scheme(self):
        value = "youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(value), "dQw4w9WgXcQ")

    def test_extract_from_plain_id(self):
        self.assertEqual(extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_extract_invalid_returns_none(self):
        self.assertIsNone(extract_video_id("https://vimeo.com/123"))

    def test_canonical_url(self):
        self.assertEqual(
            canonical_video_url("dQw4w9WgXcQ"),
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

    def test_normalize_ref(self):
        ref = normalize_youtube_ref("https://youtu.be/dQw4w9WgXcQ")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.video_id, "dQw4w9WgXcQ")
        self.assertEqual(
            ref.canonical_url,
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )


if __name__ == "__main__":
    unittest.main()
