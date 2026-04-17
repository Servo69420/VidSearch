import unittest

from app.rag import RAGPipeline, RetrievedChunk


class _FakeEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.2] * 1024 for _ in texts]


class _FakeDB:
    async def fetch(self, query, transcription_id, vector, top_k):
        _ = (query, transcription_id, vector, top_k)
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


if __name__ == "__main__":
    unittest.main()
