import unittest

from src.chunking import chunk_pages
from src.pdf_processor import PageText


class ChunkingTests(unittest.TestCase):
    def test_chunks_preserve_page_metadata(self):
        pages = [
            PageText(page_number=1, text="alpha beta gamma " * 30),
            PageText(page_number=2, text="delta epsilon zeta " * 30),
        ]

        chunks = chunk_pages(pages, "demo.pdf", chunk_size_words=20, overlap_words=5)

        self.assertTrue(chunks)
        self.assertEqual({chunk.document_name for chunk in chunks}, {"demo.pdf"})
        self.assertIn(1, {chunk.page_number for chunk in chunks})
        self.assertIn(2, {chunk.page_number for chunk in chunks})
        for chunk in chunks:
            if chunk.page_number == 1:
                self.assertNotIn("delta", chunk.text)
            if chunk.page_number == 2:
                self.assertNotIn("alpha", chunk.text)

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            chunk_pages([PageText(1, "hello world")], "demo.pdf", 10, 10)


if __name__ == "__main__":
    unittest.main()

