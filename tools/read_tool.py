"""Verb-oriented file reading backed by the shared tools interface.

The tools interface delegates to file_manager_service, the single access
boundary: every path is validated against allowed_paths.json and constrained
to the active file-manager root.
The latest read is mirrored into the workspace scratchpad so downstream
tools (edit/write) can reference or modify it without re-reading the source.
"""

import json
from pathlib import Path

from agentMemory import interface as agent_memory
from core_engine.tool_catalog import tool
from tools import interface

MAX_READ_SIZE_BYTES = 1_000_000  # ~1 MB. Raise or lower this cap here.
MAX_DOCUMENT_BYTES = 25_000_000
MAX_EXTRACTED_TEXT_BYTES = 1_000_000
_UTF8 = "utf-8"
DOCLING_EXTENSIONS = {".pdf", ".docx", ".pptx", ".odt"}
_DOC_CONVERTER = None


def _get_docling_converter():
    global _DOC_CONVERTER
    if _DOC_CONVERTER is None:
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise RuntimeError(
                "Docling is required to read PDF, DOCX, PPTX, and ODT files. "
                "Install the project's dependencies and try again."
            ) from exc

        pdf_options = PdfPipelineOptions()
        pdf_options.do_ocr = True
        _DOC_CONVERTER = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
            }
        )
    return _DOC_CONVERTER


def _read_content(path: str) -> tuple[dict, str]:
    extension = Path(path).suffix.lower()
    is_document = extension in DOCLING_EXTENSIONS
    max_bytes = MAX_DOCUMENT_BYTES if is_document else MAX_READ_SIZE_BYTES

    try:
        source = interface.read_file_bytes(path, max_bytes)
    except interface.FileReadLimitError as exc:
        if is_document:
            raise ValueError(
                f"Cannot read document '{path}': it exceeds the {MAX_DOCUMENT_BYTES}-byte "
                f"limit ({MAX_DOCUMENT_BYTES // 1_000_000} MB). Split or compress the file "
                "and try again."
            ) from exc
        raise ValueError(
            f"Cannot read '{path}': it exceeds the {MAX_READ_SIZE_BYTES}-byte "
            "text-file limit. Split the file or use a smaller file."
        ) from exc

    if is_document:
        converter = _get_docling_converter()
        try:
            result = converter.convert(str(source["resolved_path"]))
            content = result.document.export_to_markdown()
        except Exception as exc:
            raise RuntimeError(
                f"Docling could not extract text from '{path}'. The document may be "
                "encrypted, damaged, unsupported, or image-only. Try an unprotected, "
                "text-searchable PDF or another supported document."
            ) from exc
        if not content or not content.strip():
            raise ValueError(
                f"Docling found no extractable text in '{path}'. It may be image-only, "
                "empty, or unsupported."
            )
        extracted_size = len(content.encode(_UTF8))
        if extracted_size > MAX_EXTRACTED_TEXT_BYTES:
            raise ValueError(
                f"Extracted text from '{path}' is {extracted_size} bytes, exceeding the "
                f"{MAX_EXTRACTED_TEXT_BYTES}-byte output limit. Split the document and "
                "try again; no partial text was returned."
            )
        return source, content

    try:
        return source, source["content"].decode(_UTF8)
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Cannot read '{path}' as UTF-8 text. Supported binary documents include "
            "PDF, DOCX, PPTX, and ODT."
        ) from exc


@tool(provider="tools")
def read_file(path: str, request: str = "") -> str:
    """Read a UTF-8 text or Docling-supported document from the configured file-manager root.

    PDF, DOCX, PPTX, and ODT documents are text-extracted with Docling; OCR is enabled
    for PDFs to support scanned pages. Text files are limited to 1 MB; documents to
    25 MB and 1 MB of extracted text. Successful reads are mirrored to agent memory.
    Returns JSON with the request, path, content, and scratchpad context.
    """
    if not path or not path.strip():
        raise ValueError("A file path is required.")

    try:
        result, content = _read_content(path)
    except Exception as exc:
        raise RuntimeError(f"Could not read '{path}': {exc}") from exc

    scratchpad_result = agent_memory.store_read(result["path"], content, request)
    payload = {
        "request": request,
        "path": result["path"],
        "size_bytes": result["size_bytes"],
        "content_type": "document_text" if Path(path).suffix.lower() in DOCLING_EXTENSIONS else "text",
        "content": content,
        "scratchpad": {
            "path": scratchpad_result["path"],
            "updated_at": scratchpad_result["updated_at"],
            "context": "Latest read mirrored to agent scratchpad. Use read_agent_scratchpad to retrieve it.",
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
