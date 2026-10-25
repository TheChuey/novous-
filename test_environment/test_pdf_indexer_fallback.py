import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import fitz

from agentMemory import indexer


class TestPdfIndexerFallback(unittest.TestCase):
    def test_uses_pymupdf_when_docling_pdf_backend_cannot_load(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "text.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "PDF text remains searchable")
            document.save(pdf_path)
            document.close()

            converter = Mock()
            converter.convert.side_effect = ImportError("native parser unavailable")
            with patch.object(indexer, "_DOC_CONVERTER", converter):
                text = indexer._document_text(pdf_path)

        self.assertIn("PDF text remains searchable", text)

    def test_reports_when_fallback_cannot_extract_pdf_text(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "image-only.pdf"
            document = fitz.open()
            document.new_page()
            document.save(pdf_path)
            document.close()

            converter = Mock()
            converter.convert.side_effect = ImportError("native parser unavailable")
            with patch.object(indexer, "_DOC_CONVERTER", converter):
                with self.assertRaisesRegex(RuntimeError, "scanned PDFs require"):
                    indexer._document_text(pdf_path)


if __name__ == "__main__":
    unittest.main()
