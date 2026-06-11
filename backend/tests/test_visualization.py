import json
import unittest
from unittest.mock import AsyncMock, patch

from app.visualization import (
    MAX_VIZ_VERSIONS,
    VisualizationGenerator,
    build_visualization_block,
    extract_visualization_versions,
)


def _spec(block: str) -> dict:
    return json.loads(block[len("```vidviz\n"):-len("\n```")])


COMPLETE_DOC = (
    "<!DOCTYPE html><html><head><style>body{margin:0}</style></head>"
    "<body><h1>Viz</h1><script>console.log('ok')</script></body></html>"
)

# Real-world failure shape: the SSE stream died mid-generation, leaving the
# document cut off inside an unterminated <style> raw-text element.
TRUNCATED_DOC = (
    "<!DOCTYPE html><html><head><style>"
    "body{background:#000}.info-box{margin-top: 1"
)


def _response(content: str, finish_reason: str | None):
    return {
        "choices": [
            {
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ]
    }


class TestExtractHtml(unittest.TestCase):
    def setUp(self):
        self.gen = VisualizationGenerator(model="test-model")

    def test_accepts_complete_document(self):
        self.assertEqual(self.gen._extract_html(COMPLETE_DOC), COMPLETE_DOC)

    def test_accepts_fenced_document(self):
        fenced = f"```html\n{COMPLETE_DOC}\n```"
        self.assertEqual(self.gen._extract_html(fenced), COMPLETE_DOC)

    def test_rejects_non_markup(self):
        self.assertIsNone(self.gen._extract_html("Sorry, I cannot do that."))

    def test_rejects_unclosed_html_tag(self):
        self.assertIsNone(self.gen._extract_html(TRUNCATED_DOC))

    def test_rejects_unterminated_style(self):
        # Fragment form (no <html> wrapper) with a dangling <style>.
        self.assertIsNone(
            self.gen._extract_html("<div>hi</div><style>body{color:red")
        )

    def test_rejects_unterminated_script(self):
        self.assertIsNone(
            self.gen._extract_html(
                "<html><body><script>let x = 1;</body></html>"
            )
        )

    def test_accepts_fragment_with_balanced_tags(self):
        fragment = "<div><style>p{margin:0}</style><p>ok</p></div>"
        self.assertEqual(self.gen._extract_html(fragment), fragment)


class TestGenerateFinishReason(unittest.IsolatedAsyncioTestCase):
    async def _generate(self, content: str, finish_reason: str | None):
        gen = VisualizationGenerator(model="test-model")
        with patch(
            "app.visualization._call_openrouter",
            AsyncMock(return_value=_response(content, finish_reason)),
        ):
            return await gen.generate("a chart", [])

    async def test_clean_stop_returns_html(self):
        result = await self._generate(COMPLETE_DOC, "stop")
        self.assertEqual(result, COMPLETE_DOC)

    async def test_length_finish_discards(self):
        result = await self._generate(COMPLETE_DOC, "length")
        self.assertIsNone(result)

    async def test_missing_finish_reason_discards(self):
        # Stream died mid-generation: no finish_reason, truncated content.
        result = await self._generate(TRUNCATED_DOC, None)
        self.assertIsNone(result)

    async def test_truncated_content_with_stop_discards(self):
        # Even a clean stop must not ship structurally broken markup.
        result = await self._generate(TRUNCATED_DOC, "stop")
        self.assertIsNone(result)


class TestBuildVisualizationBlock(unittest.TestCase):
    def test_block_carries_title_description_and_html(self):
        block = build_visualization_block(
            "<p>hi</p>", title="My viz", description="show a chart"
        )
        self.assertTrue(block.startswith("```vidviz\n"))
        self.assertTrue(block.endswith("\n```"))
        spec = _spec(block)
        self.assertEqual(spec["type"], "artifact")
        self.assertEqual(spec["data"]["title"], "My viz")
        # The frontend Regenerate button posts this back to /visualization.
        self.assertEqual(spec["data"]["description"], "show a chart")
        self.assertEqual(spec["data"]["html"], "<p>hi</p>")

    def test_regeneration_appends_version_and_activates_it(self):
        previous = [{"title": "Old", "description": "d", "html": "<p>old</p>"}]
        block = build_visualization_block(
            "<p>new</p>", title="New", description="d",
            previous_versions=previous,
        )
        data = _spec(block)["data"]
        self.assertEqual(
            [v["html"] for v in data["versions"]], ["<p>old</p>", "<p>new</p>"]
        )
        self.assertEqual(data["active"], 1)

    def test_versions_capped_dropping_oldest(self):
        previous = [
            {"title": f"v{i}", "description": "d", "html": f"<p>{i}</p>"}
            for i in range(MAX_VIZ_VERSIONS)
        ]
        block = build_visualization_block(
            "<p>new</p>", description="d", previous_versions=previous
        )
        data = _spec(block)["data"]
        self.assertEqual(len(data["versions"]), MAX_VIZ_VERSIONS)
        self.assertEqual(data["versions"][0]["html"], "<p>1</p>")
        self.assertEqual(data["versions"][-1]["html"], "<p>new</p>")
        self.assertEqual(data["active"], MAX_VIZ_VERSIONS - 1)


class TestExtractVisualizationVersions(unittest.TestCase):
    def test_content_without_block_yields_empty(self):
        self.assertEqual(extract_visualization_versions("plain answer"), [])
        self.assertEqual(extract_visualization_versions(""), [])

    def test_bare_version_shape_round_trips(self):
        block = build_visualization_block(
            "<p>x</p>", title="T", description="d"
        )
        versions = extract_visualization_versions(f"Answer.\n\n{block}")
        self.assertEqual(
            versions,
            [{"title": "T", "description": "d", "html": "<p>x</p>"}],
        )

    def test_versions_shape_round_trips(self):
        previous = [{"title": "Old", "description": "d", "html": "<p>old</p>"}]
        block = build_visualization_block(
            "<p>new</p>", title="New", description="d",
            previous_versions=previous,
        )
        versions = extract_visualization_versions(block)
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[1]["html"], "<p>new</p>")

    def test_corrupt_block_yields_empty(self):
        self.assertEqual(
            extract_visualization_versions("```vidviz\nnot json\n```"), []
        )


if __name__ == "__main__":
    unittest.main()
