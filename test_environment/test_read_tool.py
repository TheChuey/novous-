import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools import interface
from tools import read_tool


class TestReadTool(unittest.TestCase):
    def setUp(self):
        read_tool._DOC_CONVERTER = None

    def tearDown(self):
        read_tool._DOC_CONVERTER = None

    def _source(self, path: str, content: bytes = b"%PDF") -> dict:
        return {
            "path": path,
            "resolved_path": Path(path),
            "size_bytes": len(content),
            "content": content,
        }

    def test_reads_text_files_as_utf8(self):
        read_bytes = Mock()
        read_bytes.return_value = self._source("notes.txt", "hello".encode("utf-8"))

        with patch.object(read_tool.interface, "read_file_bytes", read_bytes):
            source, content = read_tool._read_content("notes.txt")

        self.assertEqual(source["path"], "notes.txt")
        self.assertEqual(content, "hello")

    def test_extracts_pdf_text_with_docling(self):
        read_bytes = Mock()
        read_bytes.return_value = self._source("manual.pdf")
        document = Mock()
        document.export_to_markdown.return_value = "# Manual"
        converter = Mock()
        converter.convert.return_value.document = document

        with (
            patch.object(read_tool.interface, "read_file_bytes", read_bytes),
            patch.object(read_tool, "_get_docling_converter", return_value=converter),
        ):
            source, content = read_tool._read_content("manual.pdf")

        self.assertEqual(content, "# Manual")
        converter.convert.assert_called_once_with("manual.pdf")

    def test_docling_converter_enables_ocr_for_pdf(self):
        input_format = object()
        input_formats = types.ModuleType("docling.datamodel.base_models")
        input_formats.InputFormat = types.SimpleNamespace(PDF=input_format)

        pipeline_options = Mock()
        pipeline_options_module = types.ModuleType("docling.datamodel.pipeline_options")
        pipeline_options_module.PdfPipelineOptions = Mock(return_value=pipeline_options)

        converter_module = types.ModuleType("docling.document_converter")
        converter_class = Mock(return_value=object())
        pdf_format_option = Mock()
        converter_module.DocumentConverter = converter_class
        converter_module.PdfFormatOption = pdf_format_option

        modules = {
            "docling": types.ModuleType("docling"),
            "docling.datamodel": types.ModuleType("docling.datamodel"),
            "docling.datamodel.base_models": input_formats,
            "docling.datamodel.pipeline_options": pipeline_options_module,
            "docling.document_converter": converter_module,
        }
        with patch.dict(sys.modules, modules):
            read_tool._get_docling_converter()

        self.assertTrue(pipeline_options.do_ocr)
        pdf_format_option.assert_called_once_with(pipeline_options=pipeline_options)
        converter_class.assert_called_once_with(
            format_options={input_format: pdf_format_option.return_value}
        )

    def test_reports_oversized_pdf_with_actionable_message(self):
        read_bytes = Mock()
        read_bytes.side_effect = interface.FileReadLimitError("over limit")

        with patch.object(read_tool.interface, "read_file_bytes", read_bytes):
            with self.assertRaisesRegex(ValueError, "25 MB.*Split or compress"):
                read_tool._read_content("manual.pdf")

    def test_reports_unreadable_pdf_without_fabricating_content(
        self,
    ):
        read_bytes = Mock()
        read_bytes.return_value = self._source("locked.pdf")
        converter = Mock()
        converter.convert.side_effect = ValueError("bad PDF")

        with (
            patch.object(read_tool.interface, "read_file_bytes", read_bytes),
            patch.object(read_tool, "_get_docling_converter", return_value=converter),
        ):
            with self.assertRaisesRegex(RuntimeError, "encrypted, damaged, unsupported"):
                read_tool._read_content("locked.pdf")

    def test_stores_extracted_document_text_in_agent_memory(
        self,
    ):
        read_content = Mock()
        store_read = Mock()
        read_content.return_value = (self._source("manual.pdf"), "# Manual")
        store_read.return_value = {
            "path": "agentMemory/data/scratchpad.json",
            "updated_at": "2026-10-21T00:00:00+00:00",
        }

        with (
            patch.object(read_tool, "_read_content", read_content),
            patch.object(read_tool.agent_memory, "store_read", store_read),
        ):
            result = json.loads(read_tool.read_file("manual.pdf", "summarize"))

        self.assertEqual(result["content"], "# Manual")
        self.assertEqual(result["content_type"], "document_text")
        store_read.assert_called_once_with("manual.pdf", "# Manual", "summarize")


if __name__ == "__main__":
    unittest.main()
