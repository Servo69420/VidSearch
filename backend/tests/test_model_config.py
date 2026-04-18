import importlib
import os
import unittest
from unittest.mock import patch


class TestModelConfig(unittest.TestCase):
    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            module = importlib.import_module("app.model_config")
            module = importlib.reload(module)

        self.assertEqual(module.MODEL_CONFIG.chat_model, "google/gemma-4-31b-it:exacto")
        self.assertEqual(module.MODEL_CONFIG.embedding_dimensions, 1024)
        self.assertGreaterEqual(module.MODEL_CONFIG.rag_embed_batch_size, 1)

    def test_phase3_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            module = importlib.import_module("app.model_config")
            module = importlib.reload(module)

        cfg = module.MODEL_CONFIG
        self.assertEqual(cfg.phase3_summary_model, "google/gemini-2.5-flash-lite")
        self.assertEqual(cfg.phase3_section_min_topic_chunks, 2)
        self.assertEqual(cfg.phase3_section_max_topic_chunks, 4)
        self.assertEqual(cfg.phase3_section_break_similarity, 0.68)

    def test_env_overrides(self):
        env = {
            "OPENROUTER_CHAT_MODEL": "model-a",
            "OPENROUTER_EMBEDDING_MODEL": "model-b",
            "OPENROUTER_PHASE2_SUMMARY_MODEL": "model-c",
            "OPENROUTER_PHASE3_SUMMARY_MODEL": "model-d",
            "OPENROUTER_TIMEOUT_S": "12.5",
            "OPENROUTER_EMBEDDING_DIMENSIONS": "2048",
            "RAG_EMBED_BATCH_SIZE": "10",
            "RAG_RETRIEVAL_TOP_K": "4",
            "PHASE2_TOPIC_MIN_LEAF_CHUNKS": "3",
            "PHASE2_TOPIC_MAX_LEAF_CHUNKS": "8",
            "PHASE2_TOPIC_BREAK_SIMILARITY": "0.7",
            "PHASE3_SECTION_MIN_TOPIC_CHUNKS": "3",
            "PHASE3_SECTION_MAX_TOPIC_CHUNKS": "6",
            "PHASE3_SECTION_BREAK_SIMILARITY": "0.55",
        }

        with patch.dict(os.environ, env, clear=True):
            module = importlib.import_module("app.model_config")
            module = importlib.reload(module)

        cfg = module.MODEL_CONFIG
        self.assertEqual(cfg.chat_model, "model-a")
        self.assertEqual(cfg.embedding_model, "model-b")
        self.assertEqual(cfg.phase2_summary_model, "model-c")
        self.assertEqual(cfg.phase3_summary_model, "model-d")
        self.assertEqual(cfg.openrouter_timeout_s, 12.5)
        self.assertEqual(cfg.embedding_dimensions, 2048)
        self.assertEqual(cfg.rag_embed_batch_size, 10)
        self.assertEqual(cfg.rag_retrieval_top_k, 4)
        self.assertEqual(cfg.phase2_topic_min_leaf_chunks, 3)
        self.assertEqual(cfg.phase2_topic_max_leaf_chunks, 8)
        self.assertEqual(cfg.phase2_topic_break_similarity, 0.7)
        self.assertEqual(cfg.phase3_section_min_topic_chunks, 3)
        self.assertEqual(cfg.phase3_section_max_topic_chunks, 6)
        self.assertEqual(cfg.phase3_section_break_similarity, 0.55)


if __name__ == "__main__":
    unittest.main()
