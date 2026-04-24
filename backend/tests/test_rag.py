import unittest

from app.rag import Chunk, ProcessedChunk, RAGPipeline, RetrievedChunk


class _FakeEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.2] * 1024 for _ in texts]


class _FakeDB:
    async def fetch(self, query, transcription_id, vector, top_k):
        _ = (query, transcription_id, vector, top_k)
        if "level = 3" in query:
            return []
        if "summary_embedding" in query:
            return [
                {
                    "id": "2ea4bc27-cdb5-48b3-84f5-5ea3fc06dccc",
                    "idx": 0,
                    "start_s": 0.0,
                    "end_s": 30.0,
                    "summary": "Video introduction",
                    "score": 0.93,
                }
            ]

        if "parent_chunk_id" in query:
            return [
                {
                    "idx": 0,
                    "start_s": 0.0,
                    "end_s": 15.0,
                    "text": "Introduction to topic",
                    "score": 0.91,
                },
                {
                    "idx": 1,
                    "start_s": 15.0,
                    "end_s": 30.0,
                    "text": "Deep explanation",
                    "score": 0.87,
                },
            ]

        return [
            {
                "idx": 0,
                "start_s": 0.0,
                "end_s": 15.0,
                "text": "Introduction to topic",
                "score": 0.91,
            },
            {
                "idx": 1,
                "start_s": 15.0,
                "end_s": 30.0,
                "text": "Deep explanation",
                "score": 0.87,
            },
        ]


class TestRAGSearch(unittest.IsolatedAsyncioTestCase):
    async def test_search_returns_retrieved_chunks(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        result = await pipeline.search(
            "6f0dd8cc-f0d4-4aef-b42b-f8322abf3df0",
            "what is the intro about",
            top_k=2,
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], RetrievedChunk)
        self.assertEqual(result[0].idx, 0)
        self.assertAlmostEqual(result[0].score, 0.91)

    async def test_search_empty_query_returns_empty(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        result = await pipeline.search(
            "6f0dd8cc-f0d4-4aef-b42b-f8322abf3df0",
            "   ",
            top_k=2,
        )
        self.assertEqual(result, [])


def _topic(
    idx: int,
    embedding: list[float],
    summary: str | None = None,
) -> ProcessedChunk:
    resolved_summary = f"summary {idx}" if summary is None else summary
    return ProcessedChunk(
        chunk_id=f"topic-{idx}",
        idx=idx,
        level=2,
        start_s=float(idx * 30),
        end_s=float((idx + 1) * 30),
        text=f"topic text {idx}",
        summary=resolved_summary,
        summary_embedding=embedding,
    )


class TestSectionGrouping(unittest.TestCase):
    def test_build_section_ranges_splits_on_low_similarity(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        topics = [
            _topic(0, [1.0, 0.0]),
            _topic(1, [1.0, 0.0]),
            _topic(2, [0.0, 1.0]),
            _topic(3, [0.0, 1.0]),
        ]

        ranges = pipeline._build_section_ranges(topics)

        self.assertEqual(ranges, [(0, 1), (2, 3)])

    def test_build_section_ranges_merges_small_tail(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        topics = [
            _topic(0, [1.0, 0.0]),
            _topic(1, [1.0, 0.0]),
            _topic(2, [1.0, 0.0]),
            _topic(3, [0.0, 1.0]),
        ]

        ranges = pipeline._build_section_ranges(topics)

        self.assertEqual(len(ranges), 1)
        start, end = ranges[0]
        self.assertEqual(end - start + 1, 4)

    def test_attach_section_parents_sets_parent_chunk_id(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        topics = [
            _topic(0, [1.0, 0.0]),
            _topic(1, [1.0, 0.0]),
            _topic(2, [0.0, 1.0]),
            _topic(3, [0.0, 1.0]),
        ]
        ranges = [(0, 1), (2, 3)]
        sections = [
            ProcessedChunk(
                chunk_id="section-0", idx=0, level=3,
                start_s=0.0, end_s=60.0, text="s0",
            ),
            ProcessedChunk(
                chunk_id="section-1", idx=1, level=3,
                start_s=60.0, end_s=120.0, text="s1",
            ),
        ]

        pipeline._attach_section_parents(topics, sections, ranges)

        self.assertEqual(topics[0].parent_chunk_id, "section-0")
        self.assertEqual(topics[1].parent_chunk_id, "section-0")
        self.assertEqual(topics[2].parent_chunk_id, "section-1")
        self.assertEqual(topics[3].parent_chunk_id, "section-1")

    def test_build_section_chunks_uses_topic_summaries(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        topic_chunks = [
            Chunk(idx=0, level=2, start_s=0.0, end_s=30.0, text="raw 0",
                  segment_start_idx=0, segment_end_idx=9),
            Chunk(idx=1, level=2, start_s=30.0, end_s=60.0, text="raw 1",
                  segment_start_idx=10, segment_end_idx=19),
        ]
        processed_topics = [
            _topic(0, [1.0, 0.0], summary="intro summary"),
            _topic(1, [1.0, 0.0], summary="follow-up summary"),
        ]

        sections = pipeline._build_section_chunks(
            topic_chunks, processed_topics, [(0, 1)]
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].level, 3)
        self.assertEqual(sections[0].start_s, 0.0)
        self.assertEqual(sections[0].end_s, 60.0)
        self.assertIn("intro summary", sections[0].text)
        self.assertIn("follow-up summary", sections[0].text)
        self.assertNotIn("raw 0", sections[0].text)

    def test_build_section_chunks_falls_back_to_raw_when_summary_empty(self):
        pipeline = RAGPipeline(_FakeDB(), embedder=_FakeEmbedder())
        topic_chunks = [
            Chunk(idx=0, level=2, start_s=0.0, end_s=30.0, text="raw 0"),
        ]
        processed_topics = [_topic(0, [1.0, 0.0], summary="")]

        sections = pipeline._build_section_chunks(
            topic_chunks, processed_topics, [(0, 0)]
        )

        self.assertIn("raw 0", sections[0].text)


class TestSectionFirstSearch(unittest.IsolatedAsyncioTestCase):
    async def test_section_first_returns_leaves_when_sections_exist(self):
        class _SectionFakeDB:
            async def fetch(self, query, *args):
                if "level = 3" in query:
                    return [
                        {
                            "id": "sec-1",
                            "idx": 0,
                            "start_s": 0.0,
                            "end_s": 120.0,
                            "summary": "Section overview",
                            "score": 0.88,
                        }
                    ]
                if "level = 2" in query and "parent_chunk_id" in query:
                    return [
                        {
                            "id": "top-1",
                            "idx": 7,
                            "start_s": 10.0,
                            "end_s": 60.0,
                            "summary": "Topic overview",
                            "score": 0.90,
                        }
                    ]
                if "level = 1" in query and "parent_chunk_id" in query:
                    return [
                        {
                            "idx": 3,
                            "start_s": 30.0,
                            "end_s": 45.0,
                            "text": "Exact leaf match",
                            "score": 0.95,
                        }
                    ]
                return []

        pipeline = RAGPipeline(_SectionFakeDB(), embedder=_FakeEmbedder())
        result = await pipeline.search(
            "6f0dd8cc-f0d4-4aef-b42b-f8322abf3df0",
            "what is this about",
            top_k=2,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].idx, 3)
        self.assertEqual(result[0].level, 1)
        self.assertAlmostEqual(result[0].score, 0.95)
        self.assertEqual(result[0].topic_summary, "Topic overview")

    async def test_section_without_topics_falls_back_to_section_hit(self):
        class _OrphanSectionFakeDB:
            async def fetch(self, query, *args):
                if "level = 3" in query:
                    return [
                        {
                            "id": "sec-1",
                            "idx": 5,
                            "start_s": 100.0,
                            "end_s": 200.0,
                            "summary": "Stub section",
                            "score": 0.70,
                        }
                    ]
                return []

        pipeline = RAGPipeline(_OrphanSectionFakeDB(), embedder=_FakeEmbedder())
        result = await pipeline.search(
            "6f0dd8cc-f0d4-4aef-b42b-f8322abf3df0",
            "anything",
            top_k=1,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].level, 3)
        self.assertEqual(result[0].idx, 5)
        self.assertEqual(result[0].text, "Stub section")

    async def test_topic_without_leaves_falls_back_to_topic_hit(self):
        class _OrphanTopicFakeDB:
            async def fetch(self, query, *args):
                if "level = 3" in query:
                    return [
                        {
                            "id": "sec-1",
                            "idx": 0,
                            "start_s": 0.0,
                            "end_s": 100.0,
                            "summary": "Sec",
                            "score": 0.80,
                        }
                    ]
                if "level = 2" in query and "parent_chunk_id" in query:
                    return [
                        {
                            "id": "top-1",
                            "idx": 2,
                            "start_s": 10.0,
                            "end_s": 50.0,
                            "summary": "Topic",
                            "score": 0.85,
                        }
                    ]
                return []

        pipeline = RAGPipeline(_OrphanTopicFakeDB(), embedder=_FakeEmbedder())
        result = await pipeline.search(
            "6f0dd8cc-f0d4-4aef-b42b-f8322abf3df0",
            "anything",
            top_k=1,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].level, 2)
        self.assertEqual(result[0].idx, 2)
        self.assertEqual(result[0].topic_summary, "Topic")


if __name__ == "__main__":
    unittest.main()
