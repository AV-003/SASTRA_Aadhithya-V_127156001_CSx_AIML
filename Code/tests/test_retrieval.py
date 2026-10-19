import unittest

from src.chunking import chunk_pages
from src.pdf_processor import pages_from_strings
from src.retrieval import LocalRetriever
from src.sample_data import SAMPLE_DOCUMENT_NAME, SAMPLE_PAGES


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        pages = pages_from_strings(SAMPLE_PAGES)
        chunks = chunk_pages(pages, SAMPLE_DOCUMENT_NAME, chunk_size_words=120, overlap_words=20)
        self.retriever = LocalRetriever(prefer_semantic=False)
        self.retriever.build(chunks)

    def test_lamp_status_question_retrieves_page_two(self):
        results = self.retriever.query("What signal reports the lamp status?", top_k=3)
        self.assertEqual(results[0].chunk.page_number, 2)
        self.assertGreater(results[0].score, 0)

    def test_insufficient_question_has_low_score(self):
        results = self.retriever.query("What is the brake pressure calibration threshold?", top_k=3)
        self.assertLess(results[0].score, 0.04)

    def test_backend_is_clear(self):
        self.assertEqual(self.retriever.backend, "tf-idf")
        self.assertTrue(any("TF-IDF fallback" in warning for warning in self.retriever.warnings))


if __name__ == "__main__":
    unittest.main()

