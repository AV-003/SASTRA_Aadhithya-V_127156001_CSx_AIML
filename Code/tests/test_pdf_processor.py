import unittest
from pathlib import Path

from scripts.create_sample_pdf import create_pdf
from src.pdf_processor import PdfProcessingError, extract_pdf_bytes, extract_pdf_path


class PdfProcessorTests(unittest.TestCase):
    def test_extracts_synthetic_pdf_with_page_numbers(self):
        path = Path(__file__).resolve().parents[1] / "tmp" / "tests" / "sample.pdf"
        create_pdf(path)

        result = extract_pdf_path(path)

        self.assertEqual(result.page_count, 3)
        self.assertEqual(result.pages[0].page_number, 1)
        self.assertIn("Light Control", result.pages[0].text)
        self.assertIn("LampStatus", result.pages[1].text)
        self.assertIn("LOW_BEAM_ON", result.pages[2].text)

    def test_rejects_unsupported_file_type(self):
        with self.assertRaises(PdfProcessingError):
            extract_pdf_bytes(b"hello", "notes.txt")

    def test_rejects_invalid_pdf_bytes(self):
        with self.assertRaises(PdfProcessingError):
            extract_pdf_bytes(b"not a pdf", "broken.pdf")


if __name__ == "__main__":
    unittest.main()
